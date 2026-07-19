# Plan: Decouple `ICamera`/`IExposure` (reconstructed)

*Reconstructed after the fact from `specs/design/icamera_iexposure.md` and commit `cc34ab14` —
written after the change landed, not before it, unlike a normal plan. Recorded here because the
change was non-trivial (interface hierarchy change affecting every camera/spectrograph module),
not because it needed re-planning.*

## Goal

Stop `ICamera`/`ISpectrograph` from forcing every implementer to carry `IExposure`'s
progress-tracking state, since some real modules (`PipelineCamera`) have no exposure to report
progress on and were publishing fabricated, never-updated `ExposureState` purely to satisfy the
inherited contract. Tracks #437.

## Architecture

`ICamera(IData, IExposure)` → `ICamera(IData)`; same for `ISpectrograph`. `ICamera`/
`ISpectrograph` become pure identity interfaces ("this module produces images via
`grab_data()`"), with no implied progress semantics. Modules that genuinely have exposure
progress declare `IExposure` explicitly alongside `ICamera` in their own base list, rather than
getting it for free. Precedent: `IVideo(IData)` already worked this way with `pyobs-gui`'s
`DEFAULT_WIDGETS` mapping `IVideo` → `VideoWidget` directly, and `CameraWidget` already treated
`IExposure` as optional via feature-detection (`has_proxy`-style checks) rather than assuming it.

## File Map

| File | Change |
|---|---|
| `pyobs/interfaces/ICamera.py` | `ICamera(IData, IExposure)` → `ICamera(IData)` |
| `pyobs/interfaces/ISpectrograph.py` | Same change |
| `pyobs/modules/camera/basecamera.py` | `BaseCamera` gains `IExposure` explicitly in its own base list |
| `pyobs/modules/spectrograph/basespectrograph.py` | `BaseSpectrograph` gains `IExposure` explicitly |
| `pyobs/modules/camera/pipelinecamera.py` | Drops `IExposure` entirely instead of publishing fabricated `ExposureState` |
| `docs/source/whatsnew-2.0.rst` | Documents the breaking interface change |
| `CHANGELOG.rst` | Entry for the change |

## Tasks

- [x] Write design doc (`specs/design/icamera_iexposure.md`, originally `DESIGN_ICamera_IExposure.md`)
- [x] Drop `IExposure` from `ICamera`/`ISpectrograph`
- [x] Add `IExposure` explicitly to `BaseCamera`/`BaseSpectrograph`
- [x] Remove fabricated `ExposureState` publication from `PipelineCamera`
- [x] Update changelog and `whatsnew-2.0.rst`
- [x] Delete design doc on landing (now restored to `specs/design/` instead, per the new
      persistent-design-doc convention)
