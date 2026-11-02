# Plan: altitude watch while tracking

Status: implemented (pyobs-core#1023)
Repos: pyobs-core (downstream config impact: pyobs-iagvt, ascom/monti drivers)
Issue: pyobs-core#1023

## Summary

`BaseTelescope` only checked `min_altitude` in `move_radec`/`move_altaz`. A tracking mount followed its
target below the limit (a sim pier went to about -6°). Add a background task in `BaseTelescope`, not a
mixin: `min_altitude`, `_position_radec` and `_lock_moving` are BaseTelescope internals.

## Design

- `_altitude_watch` runs every 5 s and calls `_altitude_watch_tick`.
- Skipped (and the previous sample cleared) when there is no observer, no finite position, the status is
  ERROR/PARKED/PARKING/INITIALIZING/ABORTING/SLEWING, or `_lock_moving` is held. UNKNOWN stays eligible.
- Fires once when `alt < min_altitude` and `alt < previous alt` (still sinking, like Ekos). Re-arms when
  alt reaches `min_altitude + 0.5°` or on a new `move_radec`/`move_altaz`.
- `altitude_action`: `stop` (default; clear tracked body, `stop_motion()`, tracking OFF), `park` (clear
  tracked body, `park()`), `none` (log only).
- Reports with one `log.error`; does not raise (a background task would be restarted/quit the module) and
  does not set `ModuleState.ERROR`. A failing action is retried on the next tick.
- Never holds `_lock_moving` when calling the action: dummy `stop_motion`/`park` take it themselves.
- `open()` warns once if the driver does not override `_position_radec` (ascom and monti currently don't).

## Not done / follow-ups

- Dummy simulator does not hold alt/az after `stop_motion` (its position is a fixed ICRS coordinate, so the
  reported altitude keeps falling). The watch fires once regardless.
- `WeatherAwareMixin` park does not clear body tracking.
- Running robotic tasks are not told about an altitude stop (possible new event).
- No altitude guard inside the `_track_refresh_tick` nudge.
- Check iagvt (solar siderostat with default `min_altitude=10` now stops at sunset).
