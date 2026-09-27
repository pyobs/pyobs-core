# `IDataPipeline`: named, selectable pipelines applied before data is stored

Status: implemented (2026-09-27). Plan:
[`2026-09-27-data-pipeline-stack-reset.md`](../plans/2026-09-27-data-pipeline-stack-reset.md).

Repos: pyobs-core (interface, mixin, `BaseCamera`, `BaseVideo`), driver plugins (inherit it via
the base classes; pyobs-aravis and pyobs-tis override `BaseVideo._finish_image()`).

Related: [`iresettable.md`](iresettable.md), [`idatastack.md`](idatastack.md).

## Problem

A camera can only store what it grabbed. Any processing (combining a stack, astrometry,
cropping, ...) happens later, in a separate `Pipeline` module or offline, and the raw file is
always written first. For stacks from video devices ([`idatastack.md`](idatastack.md)) that is
the wrong way round: a 1-2 GB raw cube should never be written when only the combined frame is
wanted.

## Decision

The module holds several named pipelines from its YAML config. A caller selects one with
`set_pipeline()`. The selected pipeline runs on every grab (`grab_data()`, every grab in
`grab_sequence()`, and on the cube in `grab_stack()`) **before** the file is written. **The
pipeline result replaces the raw data.** Only the processed result is stored and broadcast.

```python
@dataclass
class DataPipelineState:
    pipeline: str | None  # None = no pipeline, raw data is stored
    time: Time = field(default_factory=Time.now)


@dataclass
class DataPipelineCapabilities:
    pipelines: list[str] = field(default_factory=list)  # names configured in YAML


class IDataPipeline(Interface, metaclass=ABCMeta):
    """The module can run a selected, named pipeline on its data before storing it."""

    __module__ = "pyobs.interfaces"

    state = DataPipelineState
    capabilities = DataPipelineCapabilities

    @abstractmethod
    async def set_pipeline(self, pipeline: str | None = None, **kwargs: Any) -> None:
        """Select the pipeline to run on all following grabs.

        The pipeline result replaces the raw data: only the processed result is stored and
        broadcast.

        Args:
            pipeline: Name of a configured pipeline, or None to store raw data.

        Raises:
            InvalidArgumentError: If no pipeline with this name is configured.
        """
        ...
```

Both types are already supported by the wire serializer (`str | None`, `list[str]`,
`pyobs/comm/xmpp/serializer.py`).

### Why stateful, and why that's safe enough

Considered and rejected along the way:

- **Pipeline definitions passed over RPC** (`grab_data(pipeline=[{class: ...}])`). Pipelines are
  built with `get_object()`, which instantiates any class path it's given, so any XMPP peer could
  make the module instantiate arbitrary classes. Only names go over the wire.
- **A `pipeline` parameter on `grab_data()`/`grab_sequence()`.** `**kwargs` never cross the wire:
  `Proxy.execute()` binds against the *interface's* signature and sends only
  `*ba.args[1:]` (`pyobs/comm/proxy.py:124-128`), and the receiver zips the params it knows
  against what arrived (`xml_to_params()`, `pyobs/comm/xmpp/rpc.py:43-60`). So the parameter
  would have to go into `IData.grab_data()`'s own signature, adding a parameter that most
  `IData` implementors don't support and silently ignore.
- **Changing `IData` with a version bump.** Implementors inherit `IData.version` from pyobs-core,
  so every driver would advertise `IData:2` after an upgrade without doing anything, and old
  clients hard-match `IData:1` and drop the interface
  (see [`interface_versioning.md`](interface_versioning.md)).
- **Pipelines only on `grab_stack()`.** Rejected by Tim: single frames should be processable
  on request too.

The stateful setter follows the existing `set_exposure_time()`/`set_image_type()` pattern. Its
risk is a pipeline left behind by an earlier user, and since a pipeline replaces raw data that
risk is worse than a leftover exposure time. It is covered by:

1. `IResettable.reset()` restores `default_pipeline`, and every robotic script calls it first
   ([`iresettable.md`](iresettable.md)).
2. `full_reset()` (which includes `reset()`) is called automatically at module startup.
3. Every stored file carries a `PIPELINE` FITS header, so a wrong pipeline is visible afterwards.

### Configuration

New init parameters, added via `DataPipelineMixin` to `BaseCamera` and `BaseVideo`:

```yaml
class: pyobs_aravis.AravisCamera
# ...
pipelines:
  median:
    - class: pyobs.images.processors.stack.MedianStack   # does not exist yet, see combinestack.md
  astrometry:
    - class: pyobs.images.processors.detection.DaophotSourceDetection
    - class: pyobs.images.processors.astrometry.AstrometryDotNet
      url: https://...
      on_error: info        # a failed solve still stores the image
default_pipeline: null
```

- `pipelines: dict[str, list[dict[str, Any] | ImageProcessor]] | None = None`
- `default_pipeline: str | None = None`

Validation at construction, raising `ValueError` (config error, module doesn't start):
- `default_pipeline` not `None` and not a key in `pipelines`.
- A pipeline name that is empty or equal to `"none"` (case-insensitive), since `"none"` is the
  `PIPELINE` header value for "no pipeline".

The selected pipeline starts as `default_pipeline`. `full_reset()` at startup sets it again and
publishes the state.

### Mixin

`pyobs/mixins/datapipeline.py`, `DataPipelineMixin(IDataPipeline)`, shared by `BaseCamera` and
`BaseVideo`, same pattern as `DataSequenceMixin`:

- Builds one child object per configured pipeline: `self.add_child_object({"steps": steps}, _NamedPipeline)`,
  where `_NamedPipeline(Object, PipelineMixin)` is a tiny private class in the same file. Do
  **not** use `pyobs.utils.pipeline.Pipeline`: it imports `ccdproc` at module level and carries
  calibration helpers the cameras don't need.
- `_default_pipeline: str | None`, `_data_pipeline: str | None` (currently selected).
- `async def _datapipeline_open()`: publishes `DataPipelineCapabilities(pipelines=sorted(names))`
  and `DataPipelineState(pipeline=self._data_pipeline)`. Called from the host's `open()`, like
  `_datasequence_open()`. Required, otherwise `Module.startup()` logs a missing-state error.
- `async def set_pipeline(pipeline=None)`: validates, stores, publishes state. Not blocked while
  busy, same as `set_exposure_time()`: the pipeline is captured when a grab *starts*, so a
  change during a grab applies to the next one.
- `async def _run_data_pipeline(image: Image, pipeline: str | None) -> Image`:
  - Always sets `image.header["PIPELINE"] = (pipeline or "none", "Pipeline applied before storing")`.
  - If `pipeline` is `None`, returns the image unchanged.
  - Otherwise runs the named pipeline's `run_pipeline(image)` and returns the result.
  - An `ImageError` escaping the pipeline (a step with `on_error: raise`, the default) is
    re-raised as `exc.GrabImageError(f"Pipeline {pipeline} failed: {e}")`. **Nothing is
    stored in that case.** Storing the raw data instead would silently produce exactly the
    2 GB file this feature exists to avoid. Steps whose failure should not lose the frame use
    `on_error: info` or `ignore` (existing `ImageProcessor` mechanism, `pyobs/images/processor.py`).
  - Any other exception also becomes `GrabImageError`.

The pipeline runs on the event loop, like every existing `PipelineMixin` user. Processors doing
heavy numpy work (the future stack combine processors) must offload to an executor themselves.

### Where the pipeline runs

The pipeline must see the final header (all requested FITS headers, driver headers) and must run
before the filename is formatted, so the filename template can use headers the pipeline adds.

**`BaseCamera`**: in `__expose()` (`pyobs/modules/camera/basecamera.py`), after
`apply_meridian_flip(image)` and before `format_filename(image)`. The pipeline name is captured
in `grab_data()` (`pipeline = self._data_pipeline`, next to `self._exposure_time` and
`self._image_type`) and passed into `__expose()`. Drivers only implement `_expose()`, so all
`BaseCamera` drivers get this without changes (checked for pyobs-asi, pyobs-fli, pyobs-flipro,
pyobs-qhyccd, pyobs-sbig).

**`BaseVideo`**: at the start of the base `_finish_image()` (`pyobs/modules/camera/basevideo.py`),
before `format_filename()`. pyobs-aravis (`AravisCamera._finish_image()`,
`/home/husser/code/pyobs/pyobs-aravis/pyobs_aravis/araviscamera.py:88`) and pyobs-tis
(`TisCamera._finish_image()`, `/home/husser/code/pyobs/pyobs-tis/pyobs_tis/tiscamera.py:72`)
override `_finish_image(image, broadcast, image_type)`, add headers, then call `super()`. So:

- The pipeline runs *after* their headers are added. Good: e.g. a calibration step needs
  `INSTRUME`.
- `_finish_image()`'s signature must **not** change, or both overrides break. The pipeline name
  travels on the image instead, as image meta: a new `pyobs.images.meta.DataPipelineName`
  dataclass (`name: str | None`), set via `image.set_meta(...)` in `_create_image()` from
  `NextImage.pipeline`, and read in `_finish_image()` with `image.get_meta_safe(DataPipelineName)`.
- **Missing meta falls back to the currently selected pipeline** (`self._data_pipeline`). Some
  subclasses replace `_create_image()` without calling the base version, e.g. pyobs-iagvt's
  `GregoryCamera._create_image()`
  (`/home/husser/code/pyobs/pyobs-iagvt/pyobs_iagvt/modules/gregorycamera.py:146`), which
  builds its own `Image` and calls `_finish_image()` directly. Without the fallback, no pipeline
  would run for those, although they advertise `IDataPipeline`. The fallback can differ from
  the value captured at grab start only if `set_pipeline()` is called in the few milliseconds
  between frame capture and `_finish_image()`, which is acceptable under the single-operator
  assumption ([`iresettable.md`](iresettable.md)). Distinguish "meta missing" (`get_meta_safe()`
  returns `None`) from "meta present with `name=None`" (explicitly no pipeline): only the first
  falls back.
- `NextImage` gains `pipeline: str | None`, captured in `_set_image()` when the next image is
  prepared, next to `image_type=self._image_type`.

**`BaseSpectrograph`: not in scope.** `ImageProcessor` works on `pyobs.images.Image`, but
spectrographs produce `fits.HDUList`s, sometimes with extra HDUs (pyobs-iagvt's `FTS` appends
fibercamera/gregorycamera images). There are no spectrum processors to put in a pipeline. This
needs its own design once there is a concrete use case.

### Timeouts

No change to `grab_data()`'s `@timeout`. Pipelines on single frames are expected to be
near-instantaneous (Tim, 2026-09-27). Stacks get their own timeout with a configurable margin,
see [`idatastack.md`](idatastack.md).

## Not in scope

- Spectrograph pipelines (see above).
- The stack combine processors, see [`combinestack.md`](combinestack.md).
- pyobs-gui: a pipeline selector in `CameraWidget`, driven by `DataPipelineCapabilities`.
- Rejecting surplus RPC params in `xml_to_params()` instead of silently dropping them. A general
  RPC boundary issue found while designing this. Open separately.
