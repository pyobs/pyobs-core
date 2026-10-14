# Preserve valid solar resets when Astroplan's follow-up search is empty

Status: implemented 2026-10-14; pending PR merge and patch release
Issue: [pyobs-core#972](https://github.com/pyobs/pyobs-core/issues/972)
Date: 2026-10-14

## Problem and evidence

The observing-period helper introduced by #967 / PR #969 in v2.16.0 finds a valid
sunrise or sunset for a UTC date, then searches from one minute after that event to
exclude another reset on the same date. Astroplan's bounded `which="next"` search
can return a masked time when the next day's reset moves later by more than that
minute. `_events()` currently treats this as failure of the already resolved date.
`DataProvider.night()` therefore raises, including at the beginning of
`OnDemandScheduler.schedule()`.

The issue reports Astroplan 0.10.1 / Astropy 8.0.1, longitude −76°, latitude 41.2°:
sunrise changes from about 11:17:54 UTC on October 13 to 11:19:01 on October 14,
2026. Its 67-second daily drift puts the following sunrise beyond the follow-up
search window. Göttingen (9.9445° E, 51.5606° N, 200 m) reproduces this in night
mode on October 13 and day mode on April 13, when sunset moves later by about
100 seconds. Existing real-observer tests use southern October dates or a northern
sunset moving earlier; the fixed daily fake has no seasonal drift.

Local investigation reproduced the reported locations and modes with offline IERS.
An in-memory candidate accepting a masked follow-up after a valid reset passed 21
cases: October 10–16 night mode at both northern sites, and April 10–16 day mode
at Göttingen. Checks included containing bounds, the instant one microsecond before
opening, and exact closing membership in the next cycle. This is exploratory
evidence, not a committed fix or a replacement for the regressions below.

## Decision and scope

Keep the [#967 observing-period contract](2026-10-13-follow-merit-observing-night.md):
night history resets at sunrise; solar daytime history resets at sunset. Solar
telescopes still operate morning to evening, under their existing constraints.
History cycles remain astronomical, half-open intervals `[opening, closing)`;
their lengths need not be 24 hours. No configuration, archive API, operating-window,
or observing-period semantic redesign belongs in this patch.

Accept a **masked follow-up result only after at least one valid in-date event has
been collected**, and finish through the existing ambiguity check. A masked first
lookup must still fail. A next-day search, anchored independently at that day's
UTC midnight, supplies the closing event when `bounds()` needs it.

This is appropriate for this algorithm because a follow-up starts after an in-date
event and its roughly daily search covers the remaining date. Failure to locate
the next day's event in that search does not invalidate the event already found.
It is not a general assertion that masked times always mean successful completion:
Astroplan samples/interpolates crossings, and genuinely missing solar events remain
possible. In particular, a valid last event before polar conditions can be returned
for its date, but requesting a complete period must still fail if the subsequent
date cannot supply a closing event. Preserve the current finite enumeration and
one-minute reference advance; do not enlarge the step to several minutes, invent
`opening + 24 hours`, or switch to caller-dependent anchors. Those changes would
either hide seasonal cases or alter canonical event times and boundary membership.

The ambiguity guard is essential: two accepted events followed by a masked result
must raise, not return two events or select one. Unmasked nonfinite results,
conversion failures, and nonincreasing results remain errors even after a valid
event. A masked time's underlying payload need not be finite, so inspect its mask
separately before applying finite validation to an unmasked result.

## Implementation checklist

### 1. Narrow the termination condition

- [x] In `pyobs/robotic/scheduler/observingperiod.py`, separate masked-result handling
  from unmasked finite validation. When masked and `events` is nonempty, terminate
  enumeration through the unique-date guard; otherwise retain the explicit missing
  solar reset error. Keep conversion failures as errors, rather than accepting every
  `ValueError` as an exhausted search.
- [x] Ensure every successful exit checks that at most one in-date event exists.
  Share the small finalization logic if needed so masked and beyond-end exits cannot
  diverge. Preserve bounded iteration and the too-many-events failure.
- [x] Keep strictly increasing validation for every finite returned event; perform
  it before accepting a beyond-end terminal result, so that path cannot bypass the
  invariant. Retain exact `[start, end)` date filtering.
- [x] Preserve the fixed UTC midnight anchors (including the initial one-minute
  backstep), immutable per-instance mode, cached tuples, and public method signatures.
  Cache a recovered valid date normally; never cache a fabricated missing reset.
- [x] Add a brief code comment explaining the limited follow-up search and why the
  next UTC date is queried independently. Do not increase Astroplan's grid density
  or introduce a new dependency as a workaround.
- [x] Handle expected Astroplan no-crossing warnings narrowly if suppressing the
  now-successful probe: scope handling to the follow-up call and the relevant
  `TargetAlwaysUpWarning` / `TargetNeverUpWarning` categories. Preserve warnings
  from the first lookup and unrelated warnings, including IERS/ERFA diagnostics.
  Avoid broad `ignore`, global filters, or converting arbitrary warnings to success.
  Add warning-behavior coverage if warning handling changes.

### 2. Deterministic helper regressions

Extend `tests/robotic/scheduler/test_observingperiod.py`, parameterizing both modes
where applicable.

- [x] Valid in-date event then masked result returns exactly the valid event; repeated
  key/bounds calls reuse the date cache without another observer lookup. Use an
  observer keyed by requested reference/date so adjacent dates remain independent.
- [x] Two in-date events then masked result raises the ambiguous-date error, including
  through anchored `bounds()`/`key()` and date-only `bounds()`; retain the existing
  two-events-then-finite-beyond-end case.
- [x] Masked first result still fails, as do invalid conversion, unmasked nonfinite
  values, and repeated/backward finite events after a valid event. Retain finite
  beyond-date/no-in-date-event behavior and bounded-enumeration coverage.
- [x] A valid date followed by a missing next-date reset cannot produce complete
  bounds. Include real polar missing-first behavior with offline IERS or a small
  real polar regression plus deterministic missing-next-date coverage; fail before
  archive I/O whenever bounds cannot be resolved.
- [x] Retain and exercise exact UTC midnight resets, UTC/TAI equivalence, opening
  inclusion, closing exclusion, mismatched anchors, date-only bounds equivalence,
  and separation of different observer/mode instances' caches. Add a boundary case
  near the date end with a masked follow-up so accepting it cannot shift the reset.

### 3. Moving-event and caller regressions

- [x] Add real-observer cases for longitude −76°, latitude 41.2° in October night
  mode, Göttingen in October night mode, and Göttingen in April day mode. Use
  October/April 13, 2026 as focused regressions; parameterize October/April 10–16
  if measured test runtime permits. Disable IERS downloads and age checks locally
  using the existing fixture. Do not hard-code interpolated timestamps to excessive
  precision or globally suppress astronomy warnings.
- [x] Assert the relevant consecutive resets drift later by more than 60 seconds
  (equivalently their separation exceeds 86460 seconds), so the regression cannot
  silently become another harmless fixed/earlier-event test. Check `start <= t < end`,
  date-only versus anchored bounds, exact start/end membership, and one microsecond
  before the canonical start. Keep existing southern/eastern/western-longitude tests.
- [x] Exercise `DataProvider(observer).night(time)` and `period_bounds(time)` at a
  reported failing night time and with explicit `mode="day"` at Göttingen in April.
  Verify agreement with the shared period helper, including cached repeated calls.
- [x] Extend `tests/robotic/scheduler/merits/test_follow_periods.py` or the existing
  scheduler integration tests with both affected modes. Actually invoke
  `OnDemandScheduler.schedule()` using a real observer and a filtering fake archive;
  do not mock away `DataProvider.night()` or the period calculation. Verify mode
  propagation, successful prefetch, and the archive's canonical opening/closing query.
- [x] Retain nighttime post-midnight prerequisite visibility and solar morning-to-
  afternoon prerequisite visibility; ensure `FollowMerit` and `PerNightMerit` use
  the same history and reset together. Reuse existing record/evolution fixtures.
  A closing-boundary record belongs only to the next cycle, with real/evolved parity.
- [x] Assert original-loop archive prefetch and no I/O after freeze, including worker
  evaluation and empty future periods. Preserve existing full-schedule reset/evolve
  regressions; avoid changing scheduler threading or archive behavior to fix astronomy.

### 4. Validation and release

- [x] Demonstrate that the new masked-follow-up and moving-northern-event regressions
  fail on the original v2.16.0 implementation, then pass with the patch.
- [x] Run focused helper/provider/merit/scheduler tests, then scheduler and relevant
  archive suites. Run the standalone test suite (`uv run pytest tests`, matching
  CI); report any integration/XMPP service limitations separately.
- [x] Run `uv run ruff check pyobs/` as CI does, plus Ruff on changed tests;
  `uv run black --check` on changed Python files; and `uv run pyrefly check`.
  Record actual results and any pre-existing failures rather than marking these
  checks complete based on the exploratory in-memory run.
- [x] Document the regression fix in release notes and recommend a prompt patch
  release on the 2.16 line (2.16.1 if still available). The issue blocks ordinary
  northern nighttime scheduling and seasonally affects solar daytime scheduling;
  no config migration or dependency downgrade should be needed.
- [ ] After implementation and merge, update this plan/index with checks and PR,
  then update the fleet tracking entry. Confirm the released package includes the
  fix before describing the incident as released; deployment remains a separate
  operational action.

Completion requires the production patch and these checks, not merely a successful
single `key()` call: complete bounds must still validate both astronomical endpoints.


## Implementation and validation results (2026-10-14)

- Masked follow-up results retain collected resets and share the ambiguity guard with finite
  beyond-date results. Missing first resets, unmasked invalid values, nonincreasing events and
  bounded enumeration remain explicit errors. Expected no-crossing warnings are suppressed
  only for follow-up queries; first-query and unrelated warnings remain visible.
- Deterministic masked-follow-up regressions fail in both modes on the original code. A real
  41.2 N October regression also fails through DataProvider on the original helper, evaluated
  in memory without changing repository code. The corrected helper suite passes all 57 tests.
- Real regressions cover October 10–16 at 41.2 N and Göttingen in night mode and April 10–16
  at Göttingen in day mode. Every cycle has a measured daily shift exceeding 60 seconds.
  Existing frozen-worker, real/evolved history and full-schedule reset tests now cover the
  affected northern sites and both observing modes.
- Full standalone suite: 2443 passed, 26 skipped, 102 deselected, 1 xfailed; nine existing
  numerical/astrometry warnings. Tests use offline IERS. Live XMPP integration remains for
  the release workflow, which starts ejabberd.
- Ruff production and changed tests passed; Black checks passed; pyrefly: 0 errors.
- Release note added under Unreleased in CHANGELOG.md. Patch release 2.16.1 is requested
  after merge. No dependency or configuration changes are needed.
