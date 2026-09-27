# Plan: `IResettable`, `IDataPipeline`, `IDataStack`

Status: proposed (2026-09-27). Not started.

Repos: pyobs-core (all code changes in this plan), driver plugins (verification and follow-ups
only: pyobs-asi, pyobs-fli, pyobs-flipro, pyobs-qhyccd, pyobs-sbig, pyobs-aravis, pyobs-tis,
pyobs-v4l, pyobs-iagvt, pyobs-monet).

Design docs (read all three before starting, they are the source of truth for behavior):
- [`specs/design/iresettable.md`](../design/iresettable.md)
- [`specs/design/idatapipeline.md`](../design/idatapipeline.md)
- [`specs/design/idatastack.md`](../design/idatastack.md)

## Goal

1. `IResettable.reset()`: restore per-acquisition settings to defaults, called by robotic scripts
   before they configure a camera. `IResettable.full_reset()`: `reset()` plus hardware state
   (cooling etc.), called automatically at startup.
2. `IDataPipeline.set_pipeline()`: select a named, YAML-configured pipeline that runs on every
   grab before storing. The result replaces raw data.
3. `IDataStack.grab_stack(count)`: grab N consecutive frames into one 3D cube, which the
   selected pipeline can then combine.

Implemented in `BaseCamera` and `BaseVideo`. `BaseSpectrograph` gets `IResettable` only.
No existing interface changes signature, no interface version bump.

## Ground rules for the implementer

- Order matters: phases 1 to 5 build on each other. Run the checks at the end of every phase
  before moving on.
- Checks: `ruff check pyobs tests`, `black --check pyobs tests`, `pyrefly check`,
  `pytest tests -m "not integration and not xmpp"`. **Type checker is pyrefly, never mypy.**
- Match the surrounding code: docstring style (Google style, `Args:`/`Returns:`/`Raises:`),
  `log = logging.getLogger(__name__)`, `__module__ = "pyobs.interfaces"` / `"pyobs.mixins"`,
  `__all__` at the bottom of every file, exceptions from `pyobs.utils.exceptions as exc`.
- Every new interface must be exported from `pyobs/interfaces/__init__.py` (import and
  `__all__`), every new mixin from `pyobs/mixins/__init__.py`.
- Every new interface that declares `state` must have its state published in the host's
  `open()`. Otherwise `Module.startup()` logs an error (`pyobs/modules/module.py:388`).
- Do not commit or push. Leave all changes in the working tree for review.
- If something in the design docs turns out to be wrong against the real code, stop and report
  it instead of improvising a different design.

## File map

| File | Change |
|---|---|
| `pyobs/interfaces/IResettable.py` | New: `IResettable` |
| `pyobs/interfaces/IDataPipeline.py` | New: `IDataPipeline`, `DataPipelineState`, `DataPipelineCapabilities` |
| `pyobs/interfaces/IDataStack.py` | New: `IDataStack(IAbortable)`, `DataStackState` |
| `pyobs/interfaces/__init__.py` | Export the three new interfaces and their dataclasses |
| `pyobs/images/meta/datapipeline.py` | New: `DataPipelineName` meta dataclass |
| `pyobs/images/meta/__init__.py` | Export `DataPipelineName` |
| `pyobs/images/image.py` | NAXIS for 3D, `is_color` excludes cubes, new `frames` table |
| `pyobs/mixins/datapipeline.py` | New: `DataPipelineMixin`, private `_NamedPipeline` |
| `pyobs/mixins/__init__.py` | Export `DataPipelineMixin` |
| `pyobs/modules/module.py` | `startup()` calls `full_reset()` for `IResettable` modules |
| `pyobs/modules/camera/dummycamera.py` | `full_reset()` override restoring initial cooling |
| `pyobs/modules/camera/basecamera.py` | `IResettable`, `DataPipelineMixin`, `IDataStack`; `__expose()` split; meridian flip fix |
| `pyobs/modules/camera/basevideo.py` | `IResettable`, `DataPipelineMixin`, `IDataStack`, `abort()`; pipeline in `_finish_image()` |
| `pyobs/modules/camera/basespectrograph.py` | `IResettable` (busy check only) |
| `pyobs/robotic/scripts/imaging/imaging.py` | Call `reset()` before configuring the camera |
| `pyobs/robotic/scripts/calibration/darkbias.py` | Call `reset()` before configuring the camera |
| `pyobs/robotic/storage/lco/scripts/default.py` | Call `reset()` before configuring the camera |
| `pyobs/modules/flatfield/flatfield.py` | Call `reset()` at the start of `flat_field()` |
| `tests/interfaces/...`, `tests/images/test_image*.py`, `tests/mixins/test_datapipeline.py`, `tests/modules/camera/test_reset.py`, `tests/modules/camera/test_grab_stack.py`, `tests/modules/camera/test_grab_stack_video.py`, `tests/modules/test_module*.py` | New/extended tests (see each phase) |
| `CHANGELOG.rst` | One entry per interface |
| `specs/design/index.md`, `specs/plans/index.md` | Status updates when done |

Before creating a test file, check `tests/` for an existing file covering the same class and
extend it instead (e.g. `tests/images/`, `tests/modules/test_module*.py`).

---

## Phase 1: `Image` changes and meridian flip fix

Small, independent, and required by the stacks. Do it first.

- [x] `pyobs/images/image.py`, `Image.__init__`: replace
      ```python
      self.header["NAXIS1"] = data.shape[1]
      self.header["NAXIS2"] = data.shape[0]
      ```
      with: for `data.ndim >= 2`, `NAXIS1 = data.shape[-1]`, `NAXIS2 = data.shape[-2]`; for
      `data.ndim == 3` also `NAXIS3 = data.shape[0]`. Keep the existing `data is not None and
      self._header is not None` guard.
- [x] `Image.is_color`: add `and self.header.get("CTYPE3") != "FRAME"`.
- [x] `Image.frames`: new optional constructor argument `frames: Table | None = None` (insert
      after `catalog`, **as a keyword argument** so no positional caller breaks: add it after
      `meta`, before `*args`), stored as `self._frames` (copied like `catalog`), with a
      property and setter mirroring `catalog`. Include it in `copy()`. In `writeto()`, if
      set, append `table_to_hdu(self._frames)` with `hdu.name = "FRAMES"` (after `CAT`). In
      `_from_hdu_list()`, read `"FRAMES"` into `image._frames = Table(data["FRAMES"].data)`.
      Check `Image.__init__` callers with `grep -rn "Image(" pyobs` to confirm nobody passes
      more than `meta` positionally.
- [x] `pyobs/modules/camera/basecamera.py`, `apply_meridian_flip()`: `image.data[::-1, ::-1]`
      becomes `image.data[..., ::-1, ::-1]`.
- [x] Tests (`tests/images/`, extend the existing `Image` test file):
  - 2D image: `NAXIS1`/`NAXIS2` unchanged versus today (width in `NAXIS1`).
  - 3D `(5, 20, 30)`: `NAXIS1 == 30`, `NAXIS2 == 20`, `NAXIS3 == 5`.
  - `is_color`: `(3, 20, 30)` without `CTYPE3` is color, with `CTYPE3 = 'FRAME'` is not.
  - `frames` round-trip: `Image(..., frames=Table(...))` through `to_bytes()` and
    `from_bytes()` keeps the table, and `copy()` keeps it.
  - Meridian flip on 2D and 3D data: y and x flipped, frame axis untouched.

## Phase 2: `IResettable`

- [x] `pyobs/interfaces/IResettable.py`: exactly as in `iresettable.md` (abstract
      `reset(**kwargs)` and `full_reset(**kwargs)`, no state, no capabilities). Export it.
- [x] `pyobs/modules/module.py`, `Module.startup()`: after `await self.open()` and **before**
      the `missing_published_state()` check, call `full_reset()` if
      `isinstance(self, IResettable)`, wrapped in `try/except Exception: log.exception(...)`
      (see design doc for the exact message). Import `IResettable` locally inside the method if
      a top-level import causes a circular import (check: `pyobs.interfaces` must not import
      `pyobs.modules`).
- [x] `BaseCamera`, `BaseVideo`, `BaseSpectrograph`: `full_reset()` is just
      `await self.reset(**kwargs)`. Do not move any hardware setup out of driver `open()`
      methods in this plan; that's a per-driver follow-up (see design doc, "Behavior change for
      drivers that migrate").
- [x] `DummyCamera` (`pyobs/modules/camera/dummycamera.py`): override `full_reset()`:
      `await self.reset(**kwargs)`, then `await self.set_cooling(True, CoolingStatus().set_point)`
      (restores the `CoolingStatus` defaults the camera starts with, enabled at -10 °C). Read
      the existing `set_cooling()` and `CoolingStatus` first to confirm those defaults.
- [x] `DummyCamera`: also override `reset()`: `await BaseCamera.reset(self, **kwargs)`, then
      restore gain `10.0`, offset `0.0` (via `set_gain()`/`set_offset()`) and image format
      `ImageFormat.INT16` (via `set_image_format()`), the values from its `__init__`. Without
      this, `DummyCamera` itself would trigger the startup warning below.
- [x] **Startup warning for drivers without overrides.** Goal: every driver that hasn't been
      migrated shows up in the log on every start, so the gap can't go stale.
  - In `pyobs/interfaces/IResettable.py`, add a small marker decorator, exported with the
        interface:
        ```python
        def default_reset(func: F) -> F:
            """Marks a base-class reset()/full_reset() that doesn't know driver-specific settings."""
            func.__pyobs_default_reset__ = True  # type: ignore[attr-defined]
            return func
        ```
        (`F = TypeVar("F", bound=Callable[..., Any])`; use the same ignore style pyrefly
        accepts elsewhere in the repo, check with `grep -rn "type: ignore" pyobs/modules/module.py`.)
  - Decorate `reset()` and `full_reset()` in `BaseCamera`, `BaseVideo` and `BaseSpectrograph`
        with `@default_reset`. Do **not** decorate the `DummyCamera` overrides.
  - In `Module.startup()`, right after the `full_reset()` call (inside the same
        `isinstance(self, IResettable)` branch, outside the `try`), log one warning per gap:
    - `ICooling` implemented and `type(self).full_reset` still marked: `"%s implements
          ICooling but doesn't override full_reset(), so cooling is not reset to its configured
          defaults (see specs/design/iresettable.md)."`
    - `IGain` or `IImageFormat` implemented and `type(self).reset` still marked: same wording
          for `reset()`, naming the interface(s).
    - Check the marker with `getattr(type(self).full_reset, "__pyobs_default_reset__", False)`.
          Import `ICooling`, `IGain`, `IImageFormat` locally if needed to avoid circular imports.
  - Level `warning`, not `error`: the module works, it just doesn't reset everything.
  - Tests: a `BaseCamera` subclass implementing `ICooling` without overriding `full_reset()`
        logs the cooling warning at startup (`caplog`). `DummyCamera` logs neither warning. A
        subclass overriding `reset()` but implementing `IGain` logs no gain warning.
- [x] `BaseCamera`: add `IResettable` to the bases. Implement `reset()` per the design doc,
      steps 1 to 5. Step 6 (pipeline) comes in phase 3. Busy check: `self._camera_status !=
      ExposureStatus.IDLE or self._sequence_count_left > 0`; phase 4 adds the stack flag.
      Binning: compare with `Binning(1, 1)` from `pyobs.interfaces.IBinning`
      (`BinningCapabilities.binnings` is a `list[Binning]`). Log each skip at warning level
      with the reason.
- [x] `BaseVideo`: add `IResettable`. `reset()` sets image type to `ImageType.OBJECT` via
      `self.set_image_type()`. Busy check comes in phase 4.
- [x] `BaseSpectrograph`: add `IResettable`. `reset()` only raises `DeviceBusyError` if
      `self._spectrograph_status != ExposureStatus.IDLE or self._sequence_count_left > 0`.
- [x] Robotic scripts: insert before the first camera `set_*()` call:
      ```python
      async with self.comm.safe_proxy(self.camera, IResettable) as camera:
          if camera:
              log.info("Resetting camera to defaults...")
              await camera.reset()
      ```
  - `pyobs/robotic/scripts/imaging/imaging.py`: at the top of `_setup_instrument_config()`
    (before the `IBinning` block). It runs once per instrument config, which is correct: each
    config sets everything it needs from a clean state.
  - `pyobs/robotic/scripts/calibration/darkbias.py`: in `run()`, before the `IBinning` block.
  - `pyobs/robotic/storage/lco/scripts/default.py`: in `run()`, directly before the `IBinning`
    block (around line 187), inside the same per-config loop.
  - `pyobs/modules/flatfield/flatfield.py`, `flat_field()`: directly after
    `await self._flat_fielder.reset()` (that call is the unrelated `FlatFielder.reset()`), using
    `self.safe_proxy(self._camera, IResettable)` (`FlatField` is a module, it uses
    `self.safe_proxy`, not `self.comm.safe_proxy`; check the surrounding code). Binning set via
    `FlatField.set_binning()` is safe: it's stored in the module and applied by
    `FlatFielder._init_system()` afterwards.
  - Do **not** add it to `pyobs/robotic/utils/exptime/stellarexptime.py` or
    `pyobs/robotic/utils/skyflats/flatfielder.py`. They run inside a task that has already
    configured the camera.
- [x] Tests (`tests/modules/camera/test_reset.py`, use `DummyCamera` like
      `tests/modules/camera/test_grab_sequence.py` does, with `comm.set_state = AsyncMock()`):
  - Changed exposure time and image type are back to `0.0` / `OBJECT` after `reset()`.
  - `DummyCamera` implements `IWindow`/`IBinning`: with `comm.get_own_capabilities` mocked to
    return full-frame `WindowCapabilities` and `BinningCapabilities([Binning(1,1), Binning(2,2)])`,
    `reset()` sets binning 1x1 and window to full frame, binning first (assert call order).
  - With `get_own_capabilities` returning `None`: window reset is skipped, no exception.
  - `BinningCapabilities` without `1x1`: binning reset skipped.
  - `reset()` while `_camera_status == EXPOSING` raises `DeviceBusyError`; same while
    `_sequence_count_left > 0`.
  - `BaseSpectrograph` via `DummySpectrograph`: idle `reset()` works, busy raises.
  - `reset()` does **not** touch cooling: `DummyCamera` with a changed cooling setpoint keeps it
    after `reset()`.
  - `full_reset()` on `DummyCamera`: per-acquisition settings reset **and** cooling back to
    enabled at -10 °C. Busy raises `DeviceBusyError`.
  - `full_reset()` on a base class without override (e.g. `DummySpectrograph`, or `DummyVideo`)
    behaves exactly like `reset()`.
  - `Module.startup()`: a module implementing `IResettable` has `full_reset()` (not `reset()`)
    called once after `open()` and before state `READY`. A `full_reset()` that raises is logged
    and startup still reaches `READY`. A module without `IResettable` is unaffected. Look at
    existing startup tests in `tests/modules/` for how they build a module with a
    `LocalComm`/mock comm.
  - Scripts: one test per script that `reset()` is called before the first `set_*()`, if the
    existing tests for that script make this practical (check `tests/robotic/`). Otherwise a
    single test for `Imaging._setup_instrument_config()` is enough; note which ones were
    skipped in the plan.

## Phase 3: `IDataPipeline`

- [x] `pyobs/interfaces/IDataPipeline.py`: as in `idatapipeline.md`. Export
      `IDataPipeline`, `DataPipelineState`, `DataPipelineCapabilities`.
- [x] `pyobs/images/meta/datapipeline.py`: `@dataclass class DataPipelineName: name: str | None`.
      Export from `pyobs/images/meta/__init__.py`.
- [x] `pyobs/mixins/datapipeline.py`: `DataPipelineMixin(IDataPipeline, metaclass=ABCMeta)`
      per the design doc. Structure after `pyobs/mixins/datasequence.py`:
  - `__init__(self, pipelines=None, default_pipeline=None, **kwargs)`: validate names (non-empty,
    not `"none"` case-insensitive) and `default_pipeline`, raising `ValueError` with a clear
    message. Must call `super().__init__(**kwargs)`. The mixin needs `self.add_child_object`,
    which only exists once `Object.__init__` has run, so build the pipeline objects **after**
    `super().__init__(**kwargs)`. Check the MRO of `BaseCamera` to confirm `Object.__init__`
    runs inside that `super()` call; if it doesn't, build them lazily in `_datapipeline_open()`
    instead and note it.
  - `_NamedPipeline(Object, PipelineMixin)`: private, no extra methods. Built with
    `self.add_child_object({"steps": steps}, _NamedPipeline)`. If `add_child_object()` requires a
    `"class"` key for dicts, construct `_NamedPipeline(steps=steps)` directly and pass the
    object instead. Read `Object.add_child_object()` in `pyobs/object.py` to decide.
  - `_datapipeline_open()`, `set_pipeline()`, `_run_data_pipeline()` exactly as specified,
    including the `PIPELINE` header (`"none"` when no pipeline) and the `GrabImageError`
    wrapping. Nothing is stored when the pipeline fails.
- [x] `BaseCamera`:
  - Add `DataPipelineMixin` to the bases. Put it next to `DataSequenceMixin` and check the MRO
    still resolves (instantiate `DummyCamera` in a test).
  - Pass `pipelines`/`default_pipeline` through: they arrive via `**kwargs` into
    `super().__init__()`, which is fine as long as the mixin's `__init__` is in the chain.
    Verify with a test that `DummyCamera(pipelines={...}, default_pipeline=...)` works.
  - `open()`: `await self._datapipeline_open()` next to `_datasequence_open()`.
  - `grab_data()`: capture `pipeline = self._data_pipeline` and pass it to `__expose()`.
  - `__expose()`: after `apply_meridian_flip(image)`, `image = await self._run_data_pipeline(image, pipeline)`,
    then `format_filename(image)` as before. On `GrabImageError` from the pipeline, reset
    `self._exposure = None` before re-raising (same as the existing error paths).
  - `reset()`: add step 6, `await self.set_pipeline(self._default_pipeline)`.
- [x] `BaseVideo`:
  - Add `DataPipelineMixin` to the bases, `_datapipeline_open()` in `open()`.
  - `NextImage` gains `pipeline: str | None`. Set it in `_set_image()` where `NextImage` is
    built (`pipeline=self._data_pipeline`).
  - `_create_image()`: `image.set_meta(DataPipelineName(next_image.pipeline))` before calling
    `_finish_image()`.
  - `_finish_image()`: at the very start, read the meta with
    `meta = image.get_meta_safe(DataPipelineName)`. If `meta is None` (missing), fall back to
    `self._data_pipeline`; otherwise use `meta.name` (which may be `None`, meaning explicitly no
    pipeline). Then run `image = await self._run_data_pipeline(image, name)`. The fallback is
    for subclasses that replace `_create_image()` without calling the base version, e.g.
    pyobs-iagvt's `GregoryCamera` (see design doc). **Do not change the signature**:
    pyobs-aravis (`/home/husser/code/pyobs/pyobs-aravis/pyobs_aravis/araviscamera.py:88`) and
    pyobs-tis (`/home/husser/code/pyobs/pyobs-tis/pyobs_tis/tiscamera.py:72`) override it.
  - A pipeline failure inside `_finish_image()` must reach the waiting `grab_data()` caller as
    `GrabImageError` rather than dying in `_set_image()`. Today `_set_image()` calls
    `_create_image()` directly and the requests only see `image is None`. Catch the exception
    in `_set_image()`, log it, and mark the pending requests as failed (e.g. add an `error`
    field to `ImageRequest` that `grab_data()` raises). Keep the frame loop alive.
  - `reset()`: add `await self.set_pipeline(self._default_pipeline)`.
- [x] Tests (`tests/mixins/test_datapipeline.py`, plus camera tests):
  - Config validation: unknown `default_pipeline`, empty name, name `"None"`: `ValueError`.
  - `set_pipeline("unknown")` raises `InvalidArgumentError`; valid name and `None` publish
    `DataPipelineState`.
  - `_datapipeline_open()` publishes capabilities with sorted names and the initial state.
  - `_run_data_pipeline()` with `None`: image unchanged, `PIPELINE == "none"`.
  - With a pipeline of a test processor (define a tiny `ImageProcessor` subclass in the test
    that e.g. multiplies data by 2): data processed, `PIPELINE == name`.
  - A processor raising `ImageError` with default `on_error`: `GrabImageError`; with
    `on_error="info"`: image passes through.
  - `DummyCamera` with a pipeline selected: `grab_data()` stores the processed image (check the
    written data through the VFS the existing camera tests use), header `PIPELINE` set.
    Pipeline failure: nothing written, `GrabImageError` raised, camera back to `IDLE`.
  - The pipeline is captured at grab start: `set_pipeline()` during a running grab doesn't
    affect it.
  - `DummyVideo` with a pipeline: `grab_data()` returns a processed image, and the pipeline runs
    after headers added in a `_finish_image()` override (subclass `DummyVideo` in the test,
    add a header in `_finish_image()`, assert a test processor sees it).
  - Meta fallback: a `DummyVideo` subclass whose `_create_image()` builds its own `Image` and
    calls `_finish_image()` directly (like `GregoryCamera`) still gets the selected pipeline.
    An image with `DataPipelineName(None)` meta gets no pipeline even when one is selected.
  - `reset()` restores `default_pipeline`.

## Phase 4: `IDataStack` on `BaseCamera`

- [x] `pyobs/interfaces/IDataStack.py`: as in `idatastack.md`. Export `IDataStack`, `DataStackState`.
- [x] `BaseCamera.__init__`: new parameters `max_stack_bytes: int = 2 * 1024**3`,
      `stack_frame_overhead: float = 10.0`, `stack_timeout_margin: float = 60.0`, documented in
      the docstring. New attributes `_last_frame_nbytes: int | None = None`,
      `_stack_running = False`, `_stack_abort = False`.
- [x] Split `__expose()` into `__acquire_frame()` and `__finish_product()` as described. Run
      the full existing camera test suite after this step alone, before adding stacks: single
      grabs must behave exactly as before.
- [x] `open()`: publish `DataStackState(count_total=0, count_left=0)`.
- [x] `grab_stack()` per the design doc, decorated with `@timeout(calc_stack_timeout)`, where
      `calc_stack_timeout(camera, count=1, *args, **kwargs)` implements the formula. Check how
      `@timeout` passes arguments (`pyobs/modules/module.py:35` and the call in
      `pyobs/comm/xmpp/rpc.py`, `getattr(method, "timeout")(self._handler, **ba.arguments)`), so
      `count` actually arrives.
- [x] `FRAMES` table: `astropy.table.Table` with columns `FRAME` (int), `DATE-OBS` (str),
      `EXPTIME` (float). `DATE-END` = start of the last frame + its exposure time, ISO format
      matching the existing `DATE-OBS` format in the headers.
- [x] `abort()`: also set `self._stack_abort = True`.
- [x] `_sequence_busy()` and `reset()`'s busy check: include `self._stack_running`.
- [x] `grab_sequence()` while a stack runs: `DeviceBusyError` (falls out of `_sequence_busy()`).
- [x] Tests (`tests/modules/camera/test_grab_stack.py`, `DummyCamera(readout_time=0)`, small
      frames via its config if possible so the tests stay fast):
  - `grab_stack(3)` without pipeline: one file written, data shape `(3, ny, nx)`, `NAXIS3 == 3`,
    `CTYPE3 == 'FRAME'`, `NFRAMES == 3`, `FRAMES` table with 3 rows, `DATE-END` after
    `DATE-OBS`, `PIPELINE == 'none'`.
  - `count=1`: still 3D with `NAXIS3 == 1`.
  - `count=0`: `InvalidArgumentError`.
  - Busy: while exposing, while a sequence runs, while another stack runs: `DeviceBusyError`.
  - FITS header requests: `request_fits_headers()` called exactly twice per stack (once
    before, once after), not per frame. Mock it.
  - `_init_exposure()` called once per stack.
  - Memory cap: `max_stack_bytes` smaller than `count * frame.nbytes`: `InvalidArgumentError`
    after the first frame, nothing written. With `_last_frame_nbytes` set from an earlier grab:
    raised before any exposure.
  - Shape mismatch between frames (patch `_expose` to return a different shape on frame 2):
    `GrabImageError`, nothing written.
  - Color/3D frame: `GrabImageError`.
  - `abort()` during frame 2: `AbortedError`, nothing written, status `IDLE`,
    `DataStackState(0, 0)` published. `abort()` between two frames (patch so the abort lands
    after frame 1 finished): also aborted.
  - `DataStackState` published with decreasing `count_left`, ending with `(0, 0)` in every
    path (success, abort, error).
  - With a pipeline whose test processor collapses the cube (`data.mean(axis=0)`): stored
    product is 2D, `PIPELINE` set.
  - `calc_stack_timeout` returns the formula value for given `count`/exposure time.

## Phase 5: `IDataStack` on `BaseVideo`

- [x] `BaseVideo.__init__`: same three new parameters, with `stack_frame_overhead: float = 2.0`.
      Document in `max_stack_bytes`'s docstring that products also sit in the memory
      `DataCache` (`cache_size`), see design doc.
- [x] `StackRequest` class and `self._stack_request: StackRequest | None = None`.
- [x] `_set_image()` changes per the design doc: arm on the next frame, collect from the frame
      after that, copy into a preallocated cube, set `done` when full. Nothing slow in there.
      Progress `DataStackState` publish: `comm.set_state()` is async; if awaiting it per frame
      measurably slows `_set_image()`, publish every frame via
      `asyncio.create_task(...)` instead and keep a reference to avoid garbage collection.
      Start with a plain `await` and only change it if a test or measurement shows a problem.
- [x] `grab_stack()` with its own `@timeout` (formula in the design doc, including the one
      extra frame), including the `activate_camera()` keep-alive while waiting.
- [x] `open()`: publish `DataStackState(0, 0)`.
- [x] `abort()`: new, per the design doc. `BaseVideo` has no `abort()` today; check that no
      subclass in pyobs-core or the sibling repos defines one with a different meaning
      (`grep -rn "def abort" ../pyobs-aravis ../pyobs-tis ../pyobs-v4l`).
- [x] `reset()` busy check: `self._stack_request is not None`.
- [x] Tests (`tests/modules/camera/test_grab_stack_video.py`, `DummyVideo` with a small
      `image_size` and high `fps`, or call `_set_image()` directly with synthetic arrays, which
      is faster and deterministic; look at `tests/modules/camera/test_basevideo.py` for the
      established approach):
  - The arming frame is not collected: feed frames with distinct constant values, assert the
    cube contains frames 2..N+1.
  - Consecutive frames, shape `(count, ny, nx)`, headers as for `BaseCamera`, one header
    request per stack.
  - Frames are copied: mutate the array passed to `_set_image()` after the call, cube unchanged.
  - Memory cap before start (from `_last_image`) and after the first frame.
  - Color frame (3D input): `GrabImageError`.
  - `abort()` mid-stack: `AbortedError`, `DataStackState(0, 0)`, stack request cleared.
  - A second `grab_stack()` while one runs: `DeviceBusyError`. A `grab_data()` during a stack
    still works.
  - Keep-alive: with a short `sleep_time`, the camera is not deactivated during the stack
    (mock `_deactivate_camera`).
  - Pipeline on the cube runs after `_finish_image()` override headers (reuse the phase 3
    subclass).

## Phase 6: Docs, changelog, indexes

- [x] `CHANGELOG.rst`: add entries under the topmost unreleased section (create one above the
      latest version if there is none, following the existing format). One bullet each for
      `IResettable` (incl. `full_reset()` at startup and `reset()` in the robotic scripts), `IDataPipeline`
      (incl. "result replaces raw data" and the `PIPELINE` header), `IDataStack` (incl. cube
      format and `max_stack_bytes`), and the `Image` fixes (3D `NAXIS`, `is_color`, meridian
      flip on 3D data). Point to the design docs.
- [x] `specs/design/index.md`: the three docs are listed as *proposed*. Change to
      *implemented* once done.
- [x] `specs/plans/index.md`: change this plan's status.
- [x] This plan: tick the boxes, add a short "Deviations" section for anything that differed
      from the design docs.
- [x] Check `docs/source/` for a camera configuration page or config example that lists
      `BaseCamera`/`BaseVideo` parameters. If one exists, add `pipelines`, `default_pipeline`,
      `max_stack_bytes`, `stack_frame_overhead`, `stack_timeout_margin`.

## Deviations

- **`_NamedPipeline` construction**: the design doc anticipated
  `self.add_child_object({"steps": steps}, _NamedPipeline)` might not work since `create_object()`
  requires a `"class"` key for dict configs, and suggested constructing `_NamedPipeline(steps=steps)`
  directly as a fallback. Confirmed the dict form doesn't work; used
  `self.add_child_object(_NamedPipeline, _NamedPipeline, steps=steps)` instead (pass the class
  itself as both `config_or_object` and `object_class`) rather than constructing directly — this
  goes through `Object.get_object()`'s own comm/vfs/timezone/observer copying, and matches an
  existing precedent in the codebase (`pyobs/robotic/storage/lco/taskarchive.py`'s
  `self.add_child_object(Portal, Portal, url=url, ...)`).
- **`Image.__init__`'s new NAXIS logic**: guarded with `isinstance(getattr(data, "ndim", None), int)`
  rather than reading `data.ndim` unconditionally. Needed to keep
  `tests/images/processors/misc/test_calibration.py`'s `_CCDDataCalibrator` tests passing: they
  mock `ccdproc.ccd_process()`, so `Image.from_ccddata()` receives a `MagicMock` in place of real
  array data, and `MagicMock` doesn't support `>=` comparison on its `.ndim`. Real callers always
  pass a real `ndarray`, so this is a no-op there.
- **`BaseVideo._handle_stack_frame()` extra guard**: added an early return when
  `request.done.is_set()`. Not in the design doc, found via testing: at a high enough frame rate,
  `_set_image()` can be called again (arriving frames keep coming) after the cube fills and
  `done.set()` is called, but before `grab_stack()`'s `finally` block has cleared
  `self._stack_request` — without the guard this raises `IndexError` writing past the end of the
  cube.
- **Test coverage gaps, as allowed by the plan's own phase 2/3 wording** ("if practical", "note
  which ones were skipped"):
  - No test exists for `reset()` being called in `pyobs/robotic/storage/lco/scripts/default.py`'s
    `run()` or `pyobs/modules/flatfield/flatfield.py`'s `flat_field()`: neither file had any
    existing test exercising that code path (`default.py`'s `run()` has no test file at all;
    `flatfield.py`'s tests never mock `safe_proxy`, so the real `Object.safe_proxy()` silently
    returns `None` there today). Added coverage for `DarkBiasScript` and
    `ImagingScript._setup_instrument_config()` instead, per the plan's fallback.

## Phase 7: Sibling-repo verification (read-only, report back)

No code changes in sibling repos as part of this plan. Produce a short report (append to this
plan under "Sibling-repo findings") covering:

- [ ] Every class that subclasses `BaseCamera`, `BaseVideo` or `BaseSpectrograph`, directly or
      indirectly, in `/home/husser/code/pyobs/pyobs-*` (skip `.venv`, `.claude/worktrees`).
      Known direct subclasses (2026-09-27): `AsiCamera`, `AsiCoolCamera` (pyobs-asi),
      `FliCamera` (pyobs-fli), `FliProCamera` (pyobs-flipro), `QHYCCDCamera` (pyobs-qhyccd),
      `SbigCamera` (pyobs-sbig), `AravisCamera` (pyobs-aravis), `TisCamera` (pyobs-tis),
      `v4lCamera` (pyobs-v4l), `FTS` (pyobs-iagvt). Indirect: e.g. pyobs-monet
      `FrontendCameraSouth` via `QHYCCDBonnShutter`.
- [ ] For each: does it override `grab_data()`, `_finish_image()`, `open()` in a way that skips
      the base class, or define `reset`, `grab_stack`, `set_pipeline`, `abort` with a different
      meaning? (Known: `FTS.grab_data()` delegates to `BaseSpectrograph.grab_data()`, fine;
      `AravisCamera`/`TisCamera._finish_image()` call `super()`, fine.)
- [ ] Which ones have per-acquisition settings the base `reset()` doesn't cover (gain, offset,
      image format, trigger mode, ...). These need a driver-side `reset()` override as a
      follow-up. Known candidates: `AsiCamera` (`IGain`, `IImageFormat`), `QHYCCDCamera` (`IGain`).
- [ ] Which ones apply hardware settings in `open()` (cooling setpoint, fan, trigger mode, ...)
      that should move into a `full_reset()` override. For each, note what happens today if
      that setup fails in `open()` (does startup abort?), since after migration the failure is
      only logged. Known candidates: `FliCamera` (`self._temp_setpoint`), `AsiCoolCamera`
      (`setpoint`), and every other `ICooling` implementor.
- [ ] Which ones produce color frames (these can't stack, see design doc).
- [ ] Run each sibling repo's own test suite against the modified pyobs-core, if it has one
      and it runs standalone (`pip install -e ../pyobs-core` into that repo's environment, or
      whatever that repo's README says). Report failures, don't fix them.
- [ ] For each driver in the report, draft an issue text (title + body) in this plan under
      "Draft driver issues": which `reset()`/`full_reset()` overrides it needs, which settings
      each must restore and from which attribute/config value, which hardware setup in `open()`
      should move, what happens today when that setup fails, and a link to
      `specs/design/iresettable.md`. One issue per sibling repo, drivers of the same repo
      combined. **Do not open the issues.**

## Phase 8: Open driver issues (after merge, with Tim's go-ahead)

Only once the pyobs-core change is merged and released, so the issues can name the version that
ships `IResettable`.

- [ ] Ask Tim to confirm before opening anything. The issues are public.
- [ ] Open one issue per sibling repo from the drafts in phase 7, adding the pyobs-core version.
      Use `gh api` for the pyobs org repos (`gh issue create` works, but `gh issue view
      --comments` and `gh pr edit` fail there because of the Projects-classic bug).
      pyobs-iagvt and pyobs-monet live on GWDG GitLab, not GitHub: ask Tim where those go.
- [ ] Link the opened issues in this plan and in `specs/design/iresettable.md` ("Drivers").

## Follow-ups (not part of this plan)

- `CombineStack` image processor (`pyobs/images/processors/image/combinestack.py`): mean,
  median, sum, kappa-sigma (`astropy.stats.sigma_clip`), float32, run in an executor, 2D input
  passed through unchanged, removes `CTYPE3`/`NAXIS3`, keeps `NFRAMES` and `FRAMES`.
- Driver `reset()` overrides for extra settings, and `full_reset()` overrides with hardware
  setup moved out of `open()` (from phase 7), one driver at a time.
- pyobs-gui: pipeline selector and stack button in `CameraWidget`, reset and full-reset buttons.
- Mastermind calling `full_reset()` at the start of the night.
- RPC hardening: `xml_to_params()` silently drops surplus params. Separate issue.
- ADR or steering note on the single-operator assumption.
- `BaseSpectrograph` pipelines and stacks, if a use case appears.
