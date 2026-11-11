# Plan: shared cooling ramp for cooled cameras

Status: proposed
Repos: pyobs-core, pyobs-asi, pyobs-sbig, pyobs-fli, pyobs-flipro, pyobs-qhyccd (follow-up: pyobs-gui)
Issue: pyobs-core#1066

## Summary

`set_cooling(enabled, setpoint)` writes the final setpoint in one step in asi, sbig, fli and flipro.
qhyccd has its own step loop in `_update_cooling` (`cooling_step`/`cooling_wait`, 1 degC per 60 s,
stepping from the sensor temperature), but `set_cooling(False)` never switches the cooler off there.
Add a `CoolingRampMixin` in pyobs-core that owns `set_cooling`, moves the commanded setpoint towards
the target at a configurable degC/min, and talks to the hardware only through small driver hooks.
Warm-up (raising the setpoint or switching off) is the priority and is limited by default.

## Update 2026-11-11: shared planner, defaults

Local camera GUIs (e.g. `pyobs_asi/gui.py`) write to the SDK directly and never call `set_cooling`, so a
module-only mixin does not reach them. The step logic therefore lives in a pure planner,
`pyobs.utils.coolingramp.CoolingRamp` (no asyncio, no hardware, no timing). `next_step(commanded, enabled,
target, sensor)` returns a `RampStep` (write, enabled, setpoint, done, delay). `CoolingRampMixin` drives it from
a background task for modules; local GUIs drive it from a `QTimer`. A GUI must warn or block on close while a
ramp is running, otherwise the camera stays at an intermediate setpoint.

Decided defaults: `cooling_rate_warm=1.0`, `cooling_rate_cool=2.0` degC/min (2 is what `characterize.py`
used), `ramp=False` kwarg on `set_cooling` for an immediate change, no `DET-TTGT`, rate limits in config
only. `cooling_off_temperature` is a configurable fixed end point (default 20), with the early stop on
setpoint >= sensor + 1 degC. Warm ambient above the end point (summer dome) is not covered: set it per camera.

Status: pyobs-core part (planner, mixin, `CoolingState.target`/`ramping`, dummycamera) implemented in
the PR for #1066. Drivers and GUIs follow after the core release. Still open: what each vendor SDK's close
call does to the cooler (decides whether `cooling_warmup_on_close` should default to on per driver).

## Design

### Placement and API

- New `pyobs/mixins/coolingramp.py`, exported from `pyobs/mixins/__init__.py`. Not in `BaseCamera`:
  only some cameras cool, and `BaseVideo` or other `ICooling` modules may use it later.
- Cooperative init (see `2026-08-18-cooperative-mixin-init.md`): `__init__(..., **kwargs)` ends with
  `super().__init__(**kwargs)`. It registers one background task `_cooling_ramp_loop` (restart=True).
- The mixin implements `ICooling.set_cooling(enabled, setpoint, **kwargs)`. The signature is unchanged.
- Driver hooks (abstract, async):
  - `_set_cooling_hardware(enabled: bool, setpoint: float | None) -> None`: one immediate hardware
    write (today's driver `set_cooling` body).
  - `_get_cooling_hardware() -> tuple[bool, float | None, int | None]`: enabled, hardware setpoint
    (None if the SDK cannot read it back), power in percent.
  - `_get_sensor_temperature() -> float | None`: CCD temperature, used as the ramp start when the
    cooler is off and for the early stop during warm-up.
- Optional class attribute `_cooling_setpoint_resolution: float | None = None`. Commanded values
  are rounded to it (ASI: 1.0, since `ASI_TARGET_TEMP` is an int).
- Helper `_cooling_state(power, enabled=None, setpoint=None) -> CoolingState` for driver poll loops.
  It fills in the `target` and `ramping` fields so every publisher reports the same ramp state.
- Read-only property `cooling_ramping: bool`.

### Ramp behaviour

- `set_cooling` returns at once, without waiting for the ramp. Under `_cooling_lock` it stores the
  new target (`enabled`, `setpoint`) and wakes the loop through an `asyncio.Event`. A blocking call
  would exceed RPC timeouts (40 min for -20 to +20 degC at 1 degC/min).
- Start point (`_cooling_commanded`): the last value the mixin wrote. If none is known (startup,
  FLI without a setpoint getter), use the hardware setpoint if the cooler is on, otherwise the sensor
  temperature. This is the same as `ramp_to()` in pyobs-asi/tools/characterize.py.
- On each tick the loop moves `_cooling_commanded` by at most `cooling_ramp_step` towards the target.
  The interval is `60 * step / rate` seconds, and the rate depends on the direction (warm or cool).
  If the rate for a direction is `None`, the loop writes the target in one step.
- Enable from off: write `enabled=True` at the start point, then ramp down.
- Disable: ramp up towards `cooling_off_temperature`. Stop early once the setpoint is at least
  `sensor + 1 degC` (the cooler is idle and the sensor no longer follows). Then call
  `_set_cooling_hardware(False, None)`. fli/flipro have no off switch: their hook writes 20 degC,
  as they do now.
- Cancellation: any new `set_cooling` replaces the target, and the ramp carries on from the current
  commanded value with no jump. `set_cooling(True, <current setpoint>)` holds the current value.
  `abort()` does not touch cooling. There is no new RPC.
- Errors in a tick are logged and retried on the next tick. After 5 failures in a row, log.error
  once and keep retrying at the same interval. The loop never raises.
- `full_reset()` keeps calling `set_cooling(True, configured)`. After a restart it ramps from the
  hardware value instead of jumping.

### CoolingState during a ramp

- Add `target: float | None = None` and `ramping: bool = False` to `CoolingState`, after `enabled`
  and before `time`. Both have defaults, so positional constructors in the drivers still work.
- Wire compatibility: `_xml_to_dataclass` (pyobs/comm/xmpp/serializer.py) reads only its own fields
  (old receivers ignore the new ones). A missing child keeps the default (old senders give
  `target=None`). No `ICooling.version` bump (see `specs/design/interface_versioning.md`).
- `setpoint`: the value currently commanded on the hardware. `target`: the final value requested.
  During a disable ramp, `enabled=True`, `ramping=True`, and `target=cooling_off_temperature`.
  `enabled` turns False only after the hardware switch-off.
- FITS: `DET-TSET` is the commanded setpoint. qhyccd and fli now write the configured value, which
  is the target. Add `DET-TTGT` (target) only if the maintainer wants it.

### Config options (mixin kwargs)

| option | default | meaning |
|---|---|---|
| `cooling_rate_warm` | 1.0 | degC/min when raising the setpoint or switching off; `None` = one step |
| `cooling_rate_cool` | 1.0 | degC/min when lowering the setpoint; `None` = one step |
| `cooling_ramp_step` | 1.0 | degC per write (interval follows from the rate) |
| `cooling_off_temperature` | 20.0 | warm-up end point before switching off |
| `cooling_warmup_on_close` | False | best-effort warm-up in `close()`, bounded by the timeout below |
| `cooling_close_timeout` | 60.0 | seconds allowed for that warm-up |

The 1 degC/min default matches qhyccd today (1.0/60 s). characterize.py uses 1 degC/30 s.

### Shutdown

- Default: `close()` stops the loop (Object.close cancels background tasks) and leaves the hardware
  setpoint as it is, logging the commanded value and target. A full warm-up does not fit in a
  service stop timeout.
- With `cooling_warmup_on_close`, `close()` runs the ramp loop inline until it finishes or
  `cooling_close_timeout` passes, then logs what is left. It never switches off before the early
  stop condition.
- The real thermal-shock risk on close is the SDK close itself switching the cooler off. This must
  be checked for each vendor (see open questions).

### Driver adoption

- **dummycamera** (pyobs-core): reference adopter. Hooks map to `CoolingStatus`.
  `_cooling_thread` publishes via `_cooling_state`, and its simulated sensor follows the commanded
  setpoint.
- **asi**: mixin only on `AsiCoolCamera`. `_set_cooling_hardware` = current `_set` body,
  `_get_cooling_hardware` = `_get_cooling_status`, `_get_sensor_temperature` = `_get_temperature`.
  `_cooling_setpoint_resolution = 1.0`. `_publish_temperatures` uses `_cooling_state`. `setpoint`
  config stays for `full_reset`.
- **sbig**: hooks wrap `self._cam.set_cooling` and `get_cooling` under `_lock_active`. `_poll_cooling`
  uses `_cooling_state`. `self._setpoint` stays as the configured default.
- **fli**: split `_temp_setpoint` into `_cooling_default_setpoint` (config, used by `full_reset`) and
  the mixin's commanded value. This fixes the bug where, after `set_cooling(False)`,
  `_temp_setpoint=None` stops `full_reset()` from turning cooling back on. There is no SDK setpoint
  getter, so the hook returns `setpoint=None` and the mixin's commanded value is used. `_poll_cooling`
  and `DET-TSET` use the commanded value.
- **flipro**: as fli for the hooks. `get_temperature_set_point()` is available for the hook.
  `_temp_setpoint` stays config only.
- **qhyccd**: remove the step logic from `_update_cooling`. Keep the 1 s poll, the publishing (via
  `_cooling_state`) and the PWM>250 workaround. Change the workaround from writing `_cooling_next`
  directly to calling `set_cooling(True, current + 5)`, so it goes through the ramp target. Map the
  deprecated `cooling_step`/`cooling_wait` to `cooling_ramp_step` and
  `cooling_rate_* = step / wait * 60`, with a deprecation warning. Fix
  `set_cooling(False)` so it really switches off, and publish the real enabled state instead of
  `cooler_available`. Update README and tests (`test_constructor_defaults`,
  `test_set_cooling_disabled_publishes_no_setpoint`).

## Tests

- pyobs-core `tests/mixins/test_coolingramp.py`, with a fake module that has recording hooks and a
  short interval (patched sleep or rate 600 degC/min):
  warm and cool step sizes and direction; `None` rate gives one step; retarget mid-ramp continues
  from the commanded value; disable ramps then switches off; early stop on the sensor rule;
  start point from the hardware setpoint, from the sensor, and from the last commanded value;
  resolution rounding; hook errors do not kill the loop; close default and warm-up-on-close with
  timeout; published `target`/`ramping`.
- `tests/comm`: round-trip of the new `CoolingState` and decoding an old payload without `target`.
- `tests/modules/camera/test_reset.py`: update the dummycamera cooling tests for ramp semantics
  (assert the target, or use rate `None`).
- Each driver: hook tests with mocked SDK (qhyccd already has a test module; asi/sbig/fli/flipro
  only have `test_import.py`, so add minimal ones).

## Migration order

1. pyobs-core: `CoolingState` fields, mixin, dummycamera, tests; release (minor bump).
2. pyobs-qhyccd first (already ramps, has tests, fixes the off bug), then asi, sbig, fli, flipro.
   Each repo bumps `pyobs-core>=` to the new release.
3. pyobs-gui: show `setpoint -> target` and a ramping marker in `CoolingWidget`. Optional, since old
   GUIs keep working.
4. Hardware check per camera before deploying (watch setpoint, sensor temperature and power through
   one cool-down and one warm-up).

## Risks

- Behaviour change: `set_cooling` now returns before the target is reached. Scripts that set cooling
  and then wait for the setpoint should wait for the sensor temperature instead (`ITemperatures`).
- Some cameras may already ramp in firmware, so the two ramps stack. This is harmless but slower.
- Science frames during a ramp see a moving temperature (as today during a cool-down).
- qhyccd PWM workaround and the ramp both write the setpoint. Going through `set_cooling` keeps a
  single writer.

## Open questions for the maintainer

- Defaults: warm 1.0 and cool 1.0 degC/min? Or keep cool-down at one step (`None`)?
- Does closing the SDK switch the cooler off (ASICloseCamera, SBIG close, FLIClose, FPROCam_Close,
  CloseQHYCCD)? If so, should `close()` warm up by default, or leave the camera open-loop?
- Should `set_cooling` accept `ramp=False` in kwargs for an immediate change (expert or GUI)?
- Is `cooling_off_temperature=20` and the "setpoint >= sensor + 1 degC" early stop acceptable?
- Add `DET-TTGT` to FITS headers?
- Per-camera rate limits: config only, or also a class-level maximum rate per driver?
