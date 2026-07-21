# `ICamera`/`IExposure`: decouple camera identity from exposure-progress state

Status: implemented, closed. Tracks #437. Restored from git history (was deleted on landing,
before this repo kept a persistent design/ directory) -- see cc34ab14 and 62e100f3.

## Problem

Issue #437, as filed: "`ICamera` should not inherit from `IExposure`. For example
`IPipelineCamera` is definitely no `IExposure`. But it can't just be an `IData`, since the GUI
doesn't show a widget for `IData`." (No `IPipelineCamera` interface actually exists — the
motivating case is the real module `PipelineCamera`, `pyobs/modules/camera/pipelinecamera.py:16`,
which implements `ICamera` directly.)

`ICamera(IData, IExposure)` (`pyobs/interfaces/ICamera.py:7`) forces every `ICamera` implementer
to carry `ExposureState` (`status`/`progress`/`exposure_time_left`), even when "an exposure with
progress" doesn't semantically apply. Concrete evidence this isn't hypothetical:
`PipelineCamera.open()` unconditionally publishes a single, never-updated
`ExposureState(status=IDLE, progress=0.0, exposure_time_left=0.0)`
(`pipelinecamera.py:32-34`) purely to satisfy the inherited `IExposure` contract — `grab_data()`
(`pipelinecamera.py:36-72`) runs a pipeline and returns directly, with no in-progress exposure to
report at all. It's fabricated state, not a real implementation of the interface.

Contrast with `BaseCamera` and `BaseSpectrograph`, where `IExposure` is a meaningful, honored
contract: both push real, changing `ExposureState` that tracks actual status/progress
(`basecamera.py:126-136,174-176`; `basespectrograph.py:68-69,204`). `IExposure` isn't the wrong
interface in general — it's wrong specifically for a module that has no exposure to progress
through.

Why `ICamera` carries `IExposure` at all traces to `pyobs-gui`: `mainwindow.py`'s
`DEFAULT_WIDGETS` dict (`pyobs-gui/pyobs_gui/mainwindow.py:50-62`) assigns a widget by
`isinstance(proxy, interface)`, keyed on (among others) `ICamera` -> `CameraWidget`
(`mainwindow.py:590-591`). A module that's only `IData` isn't a key at all, so it gets no widget.
That makes "be recognized as a camera in the GUI" and "carry exposure-progress semantics" the same
requirement today, bundled into one base class, even though they're logically separate questions
(identity/discoverability vs. state shape).

## Evidence `IData`-only modules can already get GUI widgets

- `IVideo(IData)` (`pyobs/interfaces/IVideo.py:14`) does **not** inherit `IExposure`, yet
  `DEFAULT_WIDGETS` already maps it to `VideoWidget` (`mainwindow.py:59`). This is existing
  precedent that a bare-`IData` interface can be a first-class, widget-having citizen in
  `pyobs-gui` — nothing structural prevents it; `VideoWidget` just needed its own dict entry keyed
  on `IVideo`, not on `IData` itself.
- `CameraWidget` already treats `IExposure` as optional, not required: exposure-state subscription
  only happens if the proxy actually is `IExposure`, via `comm.safe_proxy`/`has_proxy`
  (`camerawidget.py:150-152`) — the same defensive pattern already used for `IExposureTime` and
  `IDataSequence` right next to it (`camerawidget.py:154-159`). If `ICamera` stopped implying
  `IExposure`, `CameraWidget`'s existing feature-detection would already degrade gracefully for a
  camera without it — no widget-side logic change is needed for this.

## Proposed change

1. **`pyobs-core`**: `ICamera(IData, IExposure)` -> `ICamera(IData)` (`ICamera.py:7`) — drop the
   `IExposure` base. `ICamera` becomes a pure identity interface: "this module produces images via
   `grab_data()`," nothing about progress semantics. Same change for `ISpectrograph` (identical
   shape, `ISpectrograph.py:7`) -> `ISpectrograph(IData)`.
2. Modules that genuinely have exposure-progress semantics declare `IExposure` explicitly
   alongside `ICamera`/`ISpectrograph` in their own bases, rather than getting it for free:
   - `BaseCamera(Module, ImageFitsHeaderMixin, ICamera, IExposureTime, IImageType, IDataSequence)`
     (`basecamera.py:49`) gains `IExposure` in that list — it already implements and pushes the
     real state, this just makes the declaration honest.
   - `BaseSpectrograph(Module, SpectrumFitsHeaderMixin, ISpectrograph)` (`basespectrograph.py:26`)
     gains `IExposure` the same way.
3. `PipelineCamera` keeps `ICamera`, drops `IExposure` entirely: remove the `ExposureState`/
   `IExposure` import (`pipelinecamera.py:6`) and the fabricated `set_state(IExposure, ...)` call
   in `open()` (`pipelinecamera.py:32-34`), instead of publishing state about an exposure that
   doesn't exist. It becomes a plain `ICamera`+`IData` module, nothing more.
4. **`pyobs-gui`**: no required change. `DEFAULT_WIDGETS[ICamera] = CameraWidget`
   (`mainwindow.py:52`) keeps working identically — `isinstance(proxy, ICamera)` doesn't care what
   `ICamera` itself extends — and `CameraWidget`'s existing `has_proxy`/`safe_proxy(IExposure)`
   checks (`camerawidget.py:150-152`) already handle a camera without `IExposure` by simply not
   showing the exposure-progress panel.

## Consequences

- A camera-like module only publishes `ExposureState` if it actually has exposure semantics to
  report — no more state that misrepresents what the module does.
- `ICamera`'s meaning narrows to match its name: "grabs images," not "grabs images and has an
  exposure clock." A future `ICamera` implementer with no meaningful exposure progress (a pipeline
  camera, a synthetic/test camera, one fronting a pre-captured buffer) no longer needs to fake
  state to satisfy the type.
- `IData` remains widget-less by default in `pyobs-gui` (no `DEFAULT_WIDGETS` entry) — still
  correct, since `IData` alone only means "produces some kind of data," not "is a recognizable
  device type." `ICamera`/`ISpectrograph`/`IVideo` are the recognizable identities layered on top,
  each already able to carry its own `DEFAULT_WIDGETS` entry independent of exposure semantics,
  matching the existing `IVideo` precedent.

## Migration / blast radius

- `pyobs-core`: `ICamera.py` (1 line), `ISpectrograph.py` (1 line), `basecamera.py` (1 line, add
  `IExposure` to bases), `basespectrograph.py` (1 line), `pipelinecamera.py` (remove ~4 lines:
  import + the fake `set_state` call in `open()`).
  Downstream driver modules that extend `BaseCamera`/`BaseSpectrograph` are unaffected — they
  inherit `IExposure` transitively through the base class either way, unchanged.
  A module that subclasses `ICamera` directly (not via `BaseCamera`/`PipelineCamera`) without
  declaring `IExposure` itself would lose it. Grepping in-tree and the driver repos present
  locally, this does happen: `pyobs-iagvt`'s `SunCamera` (`pyobs_iagvt/modules/suncamera.py:15`,
  `class SunCamera(Module, ICamera, IGain, IExposureTime)`) subclasses `ICamera` directly, not via
  `BaseCamera`. It never calls `self.comm.set_state(IExposure, ...)`, so it gets `isinstance(...,
  IExposure)` today purely for free from `ICamera` without ever honoring the contract — the same
  fabricated-conformance pattern this doc uses `PipelineCamera` to justify, which is a point in
  favor of this change rather than against it. Losing that free (unhonored) conformance is a
  behavior change for `SunCamera` in principle, but per the pyobs-iagvt maintainer it's deferred,
  not a blocker for this doc — see the `pyobs-iagvt` project memory note on this gap.
  (`pyobs-tiptilt` has a second direct-`ICamera` `SunCamera`, but that project is unused/dead and
  is excluded from consideration here.) Worth a changelog note regardless, since it narrows a
  public base class.
- `pyobs-gui`: no changes required (see point 4 above).

## Alternative considered: generalize `ExposureState` instead of splitting the interface

Rejected making `ExposureState` a shared, pipeline-agnostic "operation progress" base reused across
interfaces, which was floated during earlier discussion of this issue. That's a larger surface
change than the actual defect here (`PipelineCamera` fabricating state it doesn't have), and the
codebase already independently reinvents this status+progress+time shape per interface
(`DataSequenceState`, `AutoFocusState`, `AcquisitionState`, `GuidingState` — see the parallel note
in `DESIGN_IDataSequence.md`'s point 4), which is an existing, accepted convention here rather than
a gap this issue needs to close.

## Still open (not resolved by this doc)

- Whether `PipelineCamera` eventually wants its own dedicated GUI widget, instead of reusing
  `CameraWidget` minus its exposure-progress panel, is a UX question, not decided here.
- The "`IPipelineCamera`" name in the original issue doesn't correspond to a real interface — read
  here as informal shorthand for "a module using `ICamera` without hardware-exposure semantics." No
  new interface is proposed; `PipelineCamera` remains a plain `Module` implementing `ICamera`
  directly, as it already does today.
