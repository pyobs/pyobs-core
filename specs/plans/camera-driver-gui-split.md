# Plan: Driver/GUI split for all camera modules + qhyccd correctness review

Status: proposed
Repos: pyobs-qhyccd, pyobs-fli, pyobs-tis, pyobs-asi, pyobs-aravis, pyobs-sbig, pyobs-flipro,
pyobs-v4l

## Context

In pyobs-qhyccd, Tim split the QHYCCD SDK wrapper out of the pyobs camera module
(`QHYCCDCamera` in `qhyccdcamera.py`) into a standalone Cython driver (`QHYCCDDriver` in
`qhyccddriver.pyx`) with no pyobs dependency, then wrote `gui.py` — a standalone PySide6 app that
drives the raw `QHYCCDDriver` directly, useful for testing the camera/driver without spinning up a
full pyobs module. Goal: do the same for every camera-tier repo, and separately, review qhyccd's
driver/module/gui for correctness while it's fresh.

## Survey: current state (checked 2026-08-11)

The premise "none of this exists yet elsewhere" turned out to be wrong for most repos — 6 of 8
already have a real driver/module split *and* a `gui.py`. Only two are missing `gui.py`, and both
already have the driver split done. Scope is smaller than it looked at first ask.

| Repo | Driver already split out? | `gui.py` exists? |
|---|---|---|
| pyobs-qhyccd | yes — `qhyccddriver.pyx` (Cython) | yes |
| pyobs-asi | yes — `zwoasi` (vendor pkg, used directly) | yes |
| pyobs-aravis | yes — local `aravis.py` | yes |
| pyobs-sbig | yes — `sbigudrv` | yes |
| pyobs-flipro | yes — `fliprodriver` | yes |
| pyobs-v4l | yes — `cv2` (vendor pkg, used directly) | yes |
| pyobs-fli | yes — `flidriver.pyx` + `flibase.py` mixin | **no** |
| pyobs-tis | yes — `TIS.py` | **no** |

`pyobs-andor` (dead 2020-era `pytel`-based code, no git history) and `pyobs-tui` are archived per
`specs/steering/pyobs-project-tiers.md` — out of scope. `pyobs-zwoeaf` is an autofocuser, not a
camera — out of scope.

Shared toolkit already exists and should be reused, not reinvented: `pyobs.utils.gui.camera` in
pyobs-core (`BinningWidget`, `DataDisplayWidget`, `ExposeWidget`, `ExposureTimeWidget`,
`ImageFormatWidget`, `ListPickerDialog`, `WindowingWidget`) — every existing `gui.py` already
imports from here. New `gui.py` files should follow the same pattern (pyobs-qhyccd's `gui.py` or
pyobs-flipro's `gui.py` are the closest structural templates for fli/tis, since both wrap a custom
local driver rather than a vendor package).

## Todo: build missing gui.py (work one at a time)

- [ ] pyobs-fli — write `pyobs_fli/gui.py` driving `FliDriver` (`pyobs_fli/flidriver.pyx`)
      directly, bypassing `FliBaseMixin`/`FliCamera`. Reference surface: `list_devices`, `open`,
      `close`, `get_window_binning`, `set_binning`, `set_window`, `init_exposure`,
      `set_exposure_time`, `start_exposure`, `is_exposing`, `grab_row`, `get_temp`,
      `set_temperature`. Model structure on `pyobs-qhyccd/pyobs_qhyccd/gui.py` or
      `pyobs-flipro/pyobs_flipro/gui.py`.
- [ ] pyobs-tis — write `pyobs_tis/gui.py` driving `TIS` (`pyobs_tis/TIS.py`) directly, bypassing
      `TISCamera`. Note TIS's API is GStreamer-pipeline-based (`openDevice`, `Start_pipeline`,
      `Snap_image`, `Get_image`, `Stop_pipeline`, property get/set), a different shape than the
      exposure-driven SDKs — check whether `ExposeWidget`/`ExposureTimeWidget` even fit, or whether
      a simpler live-view widget is more honest to how the device actually works.

## Todo: qhyccd correctness review (pyobs-qhyccd)

- [ ] `qhyccddriver.pyx` — review the Cython wrapper against the QHYCCD SDK docs/headers for
      correctness. One thing already spotted worth a second look: every `Control` enum member is
      defined with a trailing comma (`CONTROL_BRIGHTNESS = CONTROL_ID.CONTROL_BRIGHTNESS,`), which
      makes each member's `.value` a 1-tuple rather than the bare int — every call site compensates
      with `.value[0]`. Not a functional bug (used consistently), but worth confirming it's
      intentional rather than an accidental trailing comma, since a future call site that forgets
      `[0]` would silently misbehave (`SetQHYCCDParam` with a tuple instead of an int).
- [ ] `qhyccdcamera.py` — review the pyobs module logic: threading/timeout wrapper
      (`_run_blocking`/`_run_blocking_or_raise`), the cooling-loop PWM-wrap workaround
      (`_update_cooling`, reads `CONTROL_CURPWM` twice per poll — comment claims this is
      intentional, confirm it still holds), window/binning math in
      `_prepare_driver_for_exposure`.
- [ ] `gui.py` — review for consistency with the module's blocking-call handling (e.g.
      `expose_single_frame()` is called directly on the Qt event-loop thread, unlike
      `get_single_frame()` which goes through `run_in_executor` — confirm this asymmetry is fine
      because the call itself doesn't block).

## Verification

- New `gui.py` files: run manually against real hardware (`python -m pyobs_fli.gui`,
  `python -m pyobs_tis.gui` or equivalent entry point) — connect, expose/snap, confirm image
  displays via `DataDisplayWidget`.
- Existing test suites (`pytest`) for pyobs-fli/pyobs-tis after any driver-layer changes uncovered
  during the qhyccd-style review, to confirm no regression.
- qhyccd review: no code changes assumed yet — first pass is read/flag, fixes go through normal
  review once findings are confirmed with Tim.
