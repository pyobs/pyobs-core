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
- [x] pyobs-tis — `pyobs_tis/gui.py` written (2026-08-11), driving `TIS` directly, bypassing
      `TisCamera`. As suspected, `ExposeWidget`/`ExposureTimeWidget` didn't fit — TIS pushes
      frames continuously via a GStreamer callback rather than on a triggered exposure, so this
      uses a Start/Stop live view instead: a new lightweight `LivePreviewWidget` (plain
      `QLabel`/`QPixmap`, not `DataDisplayWidget`) fed via a Qt `Signal` emitted from TIS's
      GStreamer thread (Qt queues the cross-thread delivery automatically), plus a generic
      `PropertyPanel` that introspects `TIS.Get_Property`/`Set_Property` — numeric ranges get a
      spinbox, booleans a checkbox, everything else (enums/buttons/strings) shows read-only since
      tcam property type strings aren't reliably decodable without SDK docs on hand.
      Driver additions needed along the way: `TIS.list_devices()` (non-interactive device
      enumeration — `selectDevice()` was interactive-`input()`-only) and `TIS.get_property_names()`
      (`List_Properties()` previously only printed, didn't return anything usable).
      `pyproject.toml` gained a `gui` extra (`pyobs-core[gui]`, `qasync`) and a `tis-gui` script
      entry point, matching pyobs-flipro's pattern.
      **Not yet run against real hardware** — Tim has no TIS camera access right now. Needs
      `python -m pyobs_tis.gui` (or `tis-gui` after `uv sync --extra gui`) verified against an
      actual device before this is trusted: connect, confirm live view updates, confirm property
      panel doesn't crash on real property types, confirm Stop/Start and window close release the
      pipeline cleanly.
      Also fixed in passing, since they blocked TIS from working at all: `tiscamera.py`'s image
      callback was an `async def` handed to a synchronous GStreamer callback slot — it was never
      awaited, so no image was ever processed. Now wrapped in a sync `_on_new_image` that does
      `asyncio.run_coroutine_threadsafe`. Also fixed a use-after-unmap in
      `TIS.__convert_sample_to_numpy` (numpy view was built after `mem.unmap()`, could read freed
      memory — now copies before unmapping) and a leak on `Start_pipeline()` failure in
      `tiscamera.py.open()` (now calls `Stop_pipeline()` before raising).

## Findings: driver/gui correctness review, all 8 repos (reviewed 2026-08-11)

Read/flag only, nothing fixed yet — fixes go through normal review once triaged with Tim. Two
cross-cutting patterns showed up repeatedly, worth fixing as a fleet-wide pass rather than
repo-by-repo: (1) most `gui.py` files call blocking SDK calls directly on the Qt event-loop thread
even though the pyobs module next to them wraps the same calls in an executor; (2) abort/cancel
handling is broken or entirely missing in most `gui.py` files.

### pyobs-qhyccd

- [ ] `qhyccdcamera.py:322` — exposure timeout is hardcoded to the default `_SDK_CALL_TIMEOUT =
      5.0`, but `expose_single_frame`/`ExpQHYCCDSingleFrame` blocks for the actual exposure
      duration per QHYCCD SDK semantics. Any exposure >5s raises `TimeoutError` — would break real
      astronomical exposures. Highest-severity finding across the whole review.
- [ ] `gui.py:72` — `expose_single_frame()` runs directly on the Qt thread (unlike
      `get_single_frame()`, which goes through `run_in_executor`); given the point above, this
      freezes the UI for the full exposure. Confirms the asymmetry flagged in the original plan
      and shows it's not actually safe.
- [ ] `qhyccddriver.pyx:82` — `CAM_HUMIDITY = CONTROL_ID.CAM_HUMIDITY` is missing the trailing
      comma every other `Control` member has, so its `.value` is a bare int, not a 1-tuple. Every
      call site unconditionally does `.value[0]`, so this is a latent `TypeError` if `CAM_HUMIDITY`
      is ever used. Not currently called anywhere — latent, not active.
- [ ] `gui.py` never calls `device.close()` on exit — camera handle leaks.
- [ ] `qhyccdcamera.py` `_run_blocking` — on timeout, the spawned thread keeps running and later
      calls `future.set_result()` on an already-cancelled future; no locking around `self._device`
      between that orphaned thread and e.g. the 1s cooling poll.

### pyobs-asi

- [ ] `asicamera.py` `_expose`'s abort path never calls `stop_exposure()` on the SDK — sensor
      keeps exposing physically after pyobs believes it aborted. `gui.py` gets this right
      (`stop_exposure()` on abort); the module doesn't.
- [ ] `asicamera.py` — no lock around SDK access between the 5s temperature-poll thread and
      exposure threads; both hit the same camera handle concurrently.
- [ ] `gui.py` — camera construction, ROI, exposure start/stop, and the status poll all run
      directly on the Qt thread, unlike `asicamera.py` which wraps every SDK call through
      `_run_blocking`.
- [ ] Possible binned-window mismatch: `asicamera.py` divides window w/h by binning before
      `set_roi`; `gui.py` passes `WindowingWidget` values straight through. Needs checking against
      what `WindowingWidget` actually returns.
- [ ] Neither file releases the camera handle on exit.

### pyobs-aravis

- [ ] `araviscamera.py:219` — `set_exposure_time()` calls the driver synchronously, bypassing the
      file's own `_run_blocking` wrapper that every other SDK call goes through, contradicting the
      file's own header comment on why blocking calls must be offloaded.
- [ ] `gui.py:19-20` — camera open + `start_acquisition_continuous()` run synchronously in
      `MainWindow.__init__` on the Qt thread; GigE discovery/handshake can take seconds.
- [ ] `gui.py:48` — `_exposure_time_changed` also calls the driver directly on the Qt thread.
- [ ] `gui.py:53,62` use the default (non-daemon) `ThreadPoolExecutor` via `run_in_executor(None,
      ...)`, while `araviscamera.py` deliberately avoids the default executor for the same calls
      (non-daemon threads block interpreter shutdown on a hung call) — drift between the two.
- [ ] `araviscamera.py` — no lock between the background poll thread (`pop_frame()`) and
      `_close_camera()` tearing down `stream`/`dev`/`cam` if deactivation happens mid-poll.
- [ ] `aravis.py:251-255` — `shutdown()` relies on `del` + refcounting to close the GigE socket
      instead of an explicit close/stop call; any surviving reference leaks the socket.
- [ ] `aravis.py:197-210` — pixel format handling only branches 8-bit vs. everything-else-as-
      uint16, ignoring actual pixel format/channel count; packed 12-bit or Bayer/color formats
      would be misread.

### pyobs-sbig

- [ ] `gui.py:63` — binning is hardcoded to `(1, 1)` in `_expose_clicked`, ignoring the binning
      widget entirely even though it's wired up elsewhere in the file.
- [ ] `gui.py` — the Abort button sets an `Event` that is never checked anywhere in the exposure
      wait loop, and no abort is ever sent to the driver. Non-functional. `sbigcamera.py._expose`
      gets this right (threads an `abort_event` through its wait loop).
- [ ] `sbigudrv.pyx` — `SBIGCam`/`SBIGImg` allocate C++ objects in `__cinit__` but define no
      `__dealloc__`, and no `close()`/disconnect method exists anywhere in the driver, camera, or
      gui — the link is never released, on any path, ever.
- [ ] `gui.py` — exposure start, the finish-poll loop, and `end_exposure()` all run directly on
      the Qt thread, duplicating (and able to drift from) `sbigcamera.py`'s
      `_run_blocking`/`_run_blocking_or_raise` executor+timeout wrapper.
- [ ] `sbigcamera.py`/`sbigfiltercamera.py` — exposures guarded by `_lock_active`, filter moves by
      a separate `_lock_motion`; nothing stops a filter move running concurrently with an exposure
      against the same non-reentrant `CSBIGCam` object.
- [ ] `sbigcamera.py:179-183` — docstring says `exposure_time` is in ms, but it's stored/used as
      seconds. Likely stale doc — check against actual SBIG SDK unit expectation.

### pyobs-flipro

- [ ] `fliprocamera.py:357` — `_abort_exposure` calls `driver.cancel_exposure()`, which doesn't
      exist on `FliProDriver` (only `stop_exposure` does). Abort always raises `AttributeError`.
      `gui.py`'s abort path doesn't call anything on the driver either — abort is broken in both
      layers here.
- [ ] `fliprodriver.pyx:91-97` — `get_api_version()` never checks the SDK's success flag and never
      returns `version` — always returns `None`.
- [ ] `fliprocamera.py:81-92` — `_run_blocking`'s wrapper doesn't catch exceptions from the
      wrapped function; they only surface as an unhandled thread exception on stderr, not via
      `log`. `close()` uses this path directly, so a failed `driver.close()` is silently treated
      as success.
- [ ] `fliprocamera.py:117-145` `open()` — if `get_capabilities()` raises after the driver already
      opened successfully, the handle is never closed (module lifecycle won't call `close()` on a
      module whose `open()` failed).
- [ ] `fliprocamera.py` — no lock between the background cooling-poll task and in-progress
      exposure threads calling into the same FLI SDK handle; thread-safety of the SDK itself is
      unverified.
- [ ] `gui.py` otherwise correctly drives `FliProDriver` directly (no `fliprocamera` import) and
      keeps readout off the Qt thread via `run_in_executor` — closest of the six to doing this
      right, still the recommended structural template per the original survey.

### pyobs-v4l

- [ ] `v4lcamera.py:93-109` — `_capture`'s `while True` loop has no `break`/`return` and no
      `try/finally`; `camera.release()` on line 109 is dead code, the `VideoCapture` handle always
      leaks on cancellation or exception.
- [ ] `v4lcamera.py:56-68` — on a `_run_blocking` timeout the spawned daemon thread keeps running;
      a later call can start a second thread hitting the same non-thread-safe `VideoCapture`
      concurrently. A timed-out `_open_camera` also leaks the handle it was still opening.
- [ ] `gui.py:43,57` — live-preview loop and manual grab both call `camera.read()` via separate
      `run_in_executor` calls with no lock between them — race on the same `VideoCapture`.
- [ ] `gui.py:18` — `cv2.VideoCapture(device)` runs synchronously in `__init__` on the Qt thread,
      unlike the module which backgrounds the same call because it can hang.

### pyobs-fli (driver split only — gui.py not built yet)

- [ ] `flidriver.pyx:383-393` `get_model()` — `model`/`len` are uninitialized `char*`/`size_t`
      passed straight into `FLIGetModel`, which expects a caller-allocated buffer + its size (same
      pattern `get_serial_string` gets right with a fixed `char serial[1024]`). Will crash or
      corrupt memory if called. Also missing `.decode('utf-8')` on the result. Fix before any
      gui.py or camera code calls this.
- [ ] `flicamera.py` — **no SDK call anywhere is executor-wrapped**, not even the per-row
      `grab_row()` readout loop; the whole module runs blocking calls directly on the event loop.
      This is a bigger architectural gap from the qhyccd reference pattern than any other repo. Fix
      this in the module before building `pyobs_fli/gui.py`, or the GUI will inherit the same
      event-loop-blocking problem from day one.
- [ ] `flibase.py:96-102` `_keep_alive` — reconnect path builds a new `FliDriver` but never calls
      `.open()` on it, and only catches `ValueError` (an `OSError` from a real USB disconnect
      propagates and kills the background task silently).
- [ ] `flicamera.py` — no cleanup/`cancel_exposure()` if a mid-readout `grab_row()` error raises
      out of `_expose`; driver is left in an unknown state.
- [ ] For whoever builds `pyobs_fli/gui.py`: `FliDriver` needs `.open()` called explicitly after
      construction (the constructor alone doesn't open the device); window/binning state lives
      only in `FliCamera`, not in the driver or mixin, so query `get_window_binning()` fresh
      rather than assuming any state.

### pyobs-tis

- [x] `tiscamera.py:43` (fixed 2026-08-11) — `self.new_image` (an `async def`) was passed as
      `ImageCallback` and invoked from `TIS.py:108` on a GStreamer streaming thread as a plain
      synchronous call, so it only ever created an unawaited coroutine. **Images were never
      actually processed.** Fixed: `open()` now captures the running event loop and registers a
      sync `_on_new_image` wrapper that does `asyncio.run_coroutine_threadsafe(self.new_image(tis),
      self._loop)`.
- [x] `TIS.py:163-169` (fixed 2026-08-11) — `mem.unmap(info)` was called before building a numpy
      view over that same buffer in `__convert_sample_to_numpy`; use-after-unmap could yield
      corrupted frame data. Fixed: the array is now `.copy()`'d before `mem.unmap()` runs.
- [x] `tiscamera.py:46-47` (fixed 2026-08-11) — if `Start_pipeline()` returned `False`, `open()`
      raised without releasing the already-created pipeline. Fixed: `Stop_pipeline()` now runs
      before the raise.
- [ ] `TIS.py:191-217` — `wait_for_image`/`Snap_image` poll `self.newsample`/`self.sample` with no
      lock while `on_new_buffer` mutates the same fields from the GStreamer thread; check-then-act
      race. Not exercised by `tiscamera.py` (which always sets a callback, so `Snap_image` is never
      called) or by the new `gui.py` (same). Left open — only matters if something starts using
      `Snap_image` instead of the callback path.
- [x] `gui.py` written (2026-08-11) — see the "build missing gui.py" entry above for what it does
      and the confirmed-good/still-needed items.

## Verification

- New `gui.py` files: run manually against real hardware (`python -m pyobs_fli.gui`,
  `python -m pyobs_tis.gui` or equivalent entry point) — connect, expose/snap, confirm image
  displays via `DataDisplayWidget`.
- Existing test suites (`pytest`) for pyobs-fli/pyobs-tis after any driver-layer changes uncovered
  during the qhyccd-style review, to confirm no regression.
- qhyccd review: no code changes assumed yet — first pass is read/flag, fixes go through normal
  review once findings are confirmed with Tim.
