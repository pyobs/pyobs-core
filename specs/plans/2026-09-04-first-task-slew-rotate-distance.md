# Plan: Mean-distance dome rotate time for the scheduler's slew/rotate estimate

Status: implemented (Repos: pyobs-core)

Follow-up to `specs/plans/2026-09-01-instrument-capability-duration-estimates.md` (§"Non-goals /
open questions" → "Representative slew/rotate distance", pyobs-core#858), which shipped
`TelescopeCapability.estimate_slew_time_s()` against a fixed placeholder distance
(`DEFAULT_SLEW_DISTANCE_DEG = 90.0`). That plan's leaf-script table only ever looked up telescope
slew rate — no script consulted `DomeCapability.rotate_rate_deg_per_s` at all, even though the
field already existed on the portal side, so a rotating-dome site's dome-move time was never
counted, not even as a mean estimate.

## History: descoped from live position

This plan originally proposed using the *live* telescope/dome position for `OnDemandScheduler`'s
first placed task in a `schedule()` call (pyobs-core#858 as first filed), mirroring how
`instrument_capabilities` is threaded through. That design is **not** what shipped — decided
against during design review (2026-09-04, issue comment on #858):

- The live-position piece would only tighten variance on an estimate that's already rate-based
  (not a flat guess) since `TelescopeCapability.estimate_slew_time_s()` landed — not fix a broken
  one.
- The camera-overhead pieces (readout time, filter-change time) that were the parent plan's
  highest-value target are already fully landed and released (pyobs-core v2.4.0).
- `OnDemandScheduler`'s recursion doesn't yield in chronological order (the postponed-task branch
  yields a later-time task before the earlier-time tasks that fill the gap before it —
  `ondemandscheduler.py:183-193`), which makes "thread a live position through only the first
  call" a real footgun to get right, for a modest accuracy gain.
- No observed operational symptom (missed slots, mis-ranked tasks) motivated it — "the models
  should be right in principle" was the actual driver, which didn't justify the added surface
  (new `TaskData` field, `StartPosition` dict keyed by module name, first-iteration-only threading
  through 4 recursive call sites, per-interface RA/Dec-vs-Alt/Az frame matching).

What survived: the dome side had a second, independent gap that has nothing to do with live
position — no script could look up `DomeCapability` at all (no `dome`-identifying field existed on
any script), so dome rotate time was never counted even as a mean-rate estimate the same way
telescope slew time already was. That's real, self-contained, and confirmed needed (iag50 has a
rotating dome) — this plan covers only that.

## Design (as implemented)

**1. `DomeCapability.estimate_rotate_time_s()`** (`pyobs/robotic/instruments.py`) — mirrors
`TelescopeCapability.estimate_slew_time_s()` exactly, same shared `DEFAULT_SLEW_DISTANCE_DEG`
placeholder (no separate dome-specific default): `None` if `rotate_rate_deg_per_s` isn't declared
or isn't positive, else `distance_deg / rotate_rate_deg_per_s`.

**2. New `dome: str | None` field** on `PointingScript`, `ImagingScript`, `AutoFocusScript`
(`Annotated[str | None, IDome]`, default `None`) — same optional/degrade-to-`None` shape as
`telescope`. A script with no `dome` configured (e.g. every MONET-fleet script — plain roofs, no
rotating dome) behaves exactly as before.

**3. `max()` combination in each script's `estimate_duration()`**: telescope and dome move in
parallel, so time-to-ready is `max(slew_time, rotate_time)`, not their sum. Falls back to the
existing flat constant (`60.0`) only when *both* are `None` (no dome configured, no capability
match, or the specific rate field unset on the matched row).

## Non-goals

- **Live telescope/dome position** — see History above; not pursued without a concrete accuracy
  problem to justify it.
- **Plain-roof open/close time** — pyobs-core#877, needs a new portal-side capability field first
  (no rate/distance concept for a plain open/close roof). This is what actually unblocks
  MONET-N/S/MONTI (`monet/pyobs-monet#3`) — none of them have a rotating dome.
- **pyobs-portal's script-builder live-edit duration estimate** — unaffected either way, already
  consumes whatever `estimate_duration()` computes.

## Test plan

- [x] `DomeCapability.estimate_rotate_time_s()` — present/absent/non-positive rate, custom
      `distance_deg` override (`tests/robotic/test_instruments.py::TestDomeCapabilityEstimateRotateTime`).
- [x] `PointingScript`/`ImagingScript`/`AutoFocusScript.estimate_duration()`: dome slower than
      telescope, telescope slower than dome, dome not configured (telescope-only, unaffected) —
      one test per case per script, in each script's own test file.
