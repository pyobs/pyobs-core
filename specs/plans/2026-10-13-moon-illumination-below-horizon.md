# Ignore Moon illumination limits below the horizon

Status: implemented, merged to develop 2026-10-13 (PR #968, c301e252); included in v2.16.0.

Issue: [pyobs-core #954](https://github.com/pyobs/pyobs-core/issues/954)

## Problem and decision

`MoonIlluminationConstraint.__call__()` currently accepts a task only when
`data.moon_illumination(time) <= max_phase`, even after the Moon has set. Its
`to_astroplan()` conversion already uses astroplan's maximum-only illumination constraint,
which accepts a Moon strictly below the horizon regardless of its illumination. Consequently,
the direct evaluator and `AstroplanScheduler` can disagree on the same request.

The agreed behavior is to ignore this constraint when Moon altitude is **strictly below
0 degrees**, matching astroplan. At exactly 0 degrees and above, illumination must still be
less than or equal to `max_phase`. Passing this constraint does not bypass any other task
constraint. The horizon is the altitude returned by the observer, with no additional twilight,
terrain, lunar-radius, or configurable horizon offset.

Reproduction at Göttingen (longitude 9.9445 degrees, latitude 51.5606 degrees, height 200 m),
with `max_phase=0.30`; values are approximate and all times are UTC:

| Time | Moon altitude | Illumination | Current direct result | Astroplan / intended result |
|---|---:|---:|---|---|
| 2026-10-18 18:00 | 13.6 degrees | 0.508 | False | False |
| 2026-10-18 20:00 | 7.3 degrees | 0.516 | False | False |
| 2026-10-18 22:00 | -5.4 degrees | 0.524 | False | True |
| 2026-10-19 00:00 | -21.8 degrees | 0.532 | False | True |
| 2026-10-19 02:00 | -39.4 degrees | 0.540 | False | True |

## Implementation checklist

- [x] Add `DataProvider.moon_altaz(time: Time) -> SkyCoord` in
      `pyobs/robotic/scheduler/dataprovider.py`, alongside `sun_altaz()`. Delegate to
      `self.observer.moon_altaz(time)` and apply the existing `@cache` convention so tasks
      evaluated at the same time reuse the altitude calculation. Use the observer's Moon
      calculation directly, rather than introducing a separate coordinate transformation.
- [x] In `pyobs/robotic/scheduler/constraints/moonilluminationconstraint.py`, return Python
      `True` immediately when `float(data.moon_altaz(time).alt.degree) < 0.0`; otherwise use
      the existing inclusive illumination comparison. This also avoids computing illumination
      when the Moon is down. Keep `to_astroplan()` as the existing maximum-only conversion.
- [x] Expand the constraint's class docstring to state both the below-horizon exemption and
      the inclusive illumination limit at/above the horizon.
- [x] Add the regression and cache tests below, then run the focused and scheduler checks.
- [x] After merge to `develop`, remove #954 and this plan
      from the fleet open-items snapshot according to that file's maintenance rule.

Keep `max_phase` validation/default, constraint cost, serialization, and request metadata
unchanged: `req_token = "MOONFRAC"`, `req_fields()["MAX"] = (max_phase, "fraction")` continue
to describe the requested limit, even when the Moon is down. No portal schema or configuration
change is required. Preserve the scheduler's dedicated single-worker executor and existing
`DataProvider` ownership; the new cached method is called within that same evaluation path,
with no new event-loop work, shared provider, or threading mechanism.

## Tests and validation

- [x] In `tests/robotic/scheduler/constraints/test_moonillumination.py`, add deterministic
      parameterized cases with controlled provider altitude and illumination values:
      below zero accepts even illumination 1.0 with `max_phase=0.0`; exactly zero and positive
      altitude each accept illumination below/equal to the threshold and reject illumination
      above it. Include a small negative altitude to make the strict boundary explicit.
      Assert Python boolean results and that the below-horizon branch skips illumination.
- [x] Update the first existing real-ephemeris case (`2025-11-05T13:00:00` UTC at longitude
      20.8108, latitude -32.3758, height 1798 m) from `False` to `True`: the Moon is about
      -51.6 degrees high despite illumination about 0.999. Check the other existing cases
      against their altitude and illumination so retained expectations describe the new rule.
- [x] Add a real-ephemeris parity regression using the Göttingen times above. Evaluate the
      direct constraint and its `to_astroplan()` result using the same observer and times;
      normalize astroplan's result shape to scalar booleans. Assert both parity and the
      explicit expected results, so agreement alone cannot hide a regression. Use the
      repository's existing offline ephemeris/IERS setup; do not depend on fresh downloads
      or assert the rounded numerical values in the table. Test the exact horizon with
      controlled values, not a numerically estimated moonset time.
- [x] Extend `tests/robotic/scheduler/test_dataprovider.py` following the `sun_altaz` spy
      test: two calls at the same time and one at a different time make exactly two observer
      calls, and the result is passed through. Verify separate provider instances do not
      share a cached Moon AltAz result.
- [x] Run `pytest tests/robotic/scheduler/constraints/test_moonillumination.py
      tests/robotic/scheduler/test_dataprovider.py`, then `pytest tests/robotic/scheduler/`
      (includes existing FITS request metadata and executor regression tests).
- [x] Run the repository's `ruff`, `black --check`, and `pyrefly` checks for the implementation;
      distinguish any pre-existing failures from regressions.

## Acceptance and rollout

- [x] Bright Moon below the horizon no longer rejects an otherwise eligible task.
- [x] At/above the horizon, the maximum phase remains inclusive and enforced.
- [x] The direct and astroplan paths agree on the reproduced pre-/post-moonset cases.
- [x] Moon altitude is cached per provider and evaluation time using the established pattern.
- [x] Request FITS cards and scheduler execution/threading behavior retain their contracts.

This is a pyobs-core behavior fix with no migration. It can make additional tasks eligible
after moonset when the Moon is brighter than their limit; that is the intended change. No
Moon separation, lunar sky-brightness model, or scheduling-window sampling changes are part
of this plan. Publication and issue closure follow PR merge and release.

## Verification results (2026-10-13)

- Focused constraint/provider tests: 17 passed.
- Scheduler suite: 101 passed, 1 skipped (6 existing ERFA dubious-year warnings).
- `ruff check pyobs/` and changed tests: passed. Whole-repository `ruff check .` has an
  existing I001 import-order error at `docs/create_rst.py:243`, confirmed against HEAD.
- `black --check .`: passed (774 files).
- `pyrefly check` using the project virtualenv interpreter: 0 errors.

Implementation is complete; publication and issue closure follow PR merge and release.
