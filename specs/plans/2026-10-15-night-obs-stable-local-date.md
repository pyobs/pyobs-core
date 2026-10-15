# Keep one local observing-night date across sunset and midnight

Status: proposed; not implemented
Issue: [pyobs-core#995](https://github.com/pyobs/pyobs-core/issues/995)
Date: 2026-10-15
Repos: pyobs-core

## Problem and evidence

`Time.night_obs()` selects previous/next sunset according to local noon, but passes
`self` to `Observer.sun_set_time()`. After sunset and before midnight, `next`
therefore selects tomorrow's sunset; after midnight, `previous` selects yesterday's.
Its final `sunset.to_datetime().date()` also takes the UTC date, which can differ
from the sunset's date at the observatory. The docstring calls the boundary solar
noon, although the code uses civil 12:00 in `observer.timezone`.

Investigation for #995 reproduced the first defect with a real Astroplan observer
at latitude 41.2°, longitude −76°, timezone UTC: October 14, 2026 at 21:00 returns
October 14; 22:20 and 23:59 return October 15; October 15 at 00:01 returns October
14 again. America/New_York exhibits the corresponding flip at local midnight.
Los Angeles (34.05°, −118.24°) in June also exposes the independent UTC-date defect:
a local June 20 sunset occurs on June 21 UTC. These are investigation findings;
this document adds no production fix or executable regression.

`FitsHeaderMixin` derives `DAY-OBS` from this helper. Its persisted frame cache
holds only the latest `{night, framenum}` and resets on any date change, including
a change backwards. The default filename combines `DAY-OBS` and `FRAMENUM`, so
returning to an earlier date can reuse filenames and risk overwriting data.
The reset depends on a configured cache; the uncached counter simply increments.
`Mastermind._next_obsnum()` also keys its persisted counter by this helper, and
`DarkBiasScript._resolve_night()` uses it for matching science exposure times.
Existing time tests cover before sunset, morning calibration and polar day, but
not an entire night or a sunset whose UTC and local dates differ.

## Contract and scope

For an ordinary site with a sunset in the anchored search window, all instants
in the half-open interval **[local civil noon, next local civil noon)** resolve to
the local calendar date of the sunset found after the opening noon. Afternoon
frames before sunset already belong to that upcoming night. Sunset, UTC midnight,
local midnight and sunrise do not change the identifier; morning calibrations
retain the preceding night until noon. Exactly noon belongs to the new interval.
Use the configured observer timezone, even if it is UTC at a western longitude;
do not infer a timezone from longitude or substitute apparent solar noon.

Compute the most recent local civil noon, search from that fixed instant with
`which="next"`, and convert the resulting sunset with `observer.timezone` before
extracting its date. Build noon from the selected local **calendar date** and
localize it with that date's timezone rules. Do not subtract 24 elapsed hours or
reuse the query's UTC offset via `replace()` across a DST transition. Support the
timezone objects accepted by the existing Observer path, including pytz; avoid a
new dependency or a broad timezone abstraction.

Preserve masked-sunset behavior: return the query's local calendar date when the
anchored search has no crossing, including polar day/night. This explicit fallback
can change at local midnight and does not promise ordinary-night counter stability.
Do not substitute an arbitrary earlier sunset, extend searches indefinitely, or
swallow unrelated errors. Near polar transitions, whether a crossing exists is
judged from the fixed noon anchor, so all calls in that interval use the same
search; the fallback date still comes from the query, not the anchor.

Keep `night_obs=False` and the no-observer FITS path unchanged: they use the
`DATE-OBS` calendar date as currently implemented, not a new site-local conversion.
Keep signatures, cache schemas, counter logic, filename templates and explicit
calibration-night overrides unchanged. Scheduler observing periods have their own
sunrise/sunset history contract; do not merge that algorithm with this helper.
Archive overwrite protection, cache concurrency, out-of-order exposures and
historical data repair are separate work.

## Implementation checklist

- [ ] Change only the noon anchor and sunset-date conversion in `pyobs/utils/time.py`;
  document civil-noon interval membership and the polar exception. Reuse the
  existing masked-result check and error propagation.
- [ ] Add real-observer regressions in `tests/utils/test_time.py`, with local offline
  IERS configuration. For the reported 41.2°/−76° site in UTC and America/New_York,
  check afternoon, before/after sunset, before/after both midnights, dawn and late
  morning all return the same expected date. Check one microsecond before noon,
  exactly noon and after noon advance once to the next night. Use explicit timezone
  conversions in fixtures and avoid brittle exact sunset timestamps.
- [ ] Add America/Los_Angeles June 20, 2026 evening/overnight samples that expect
  June 20 despite the sunset's June 21 UTC date; include an eastern-longitude
  non-UTC site to guard the opposite conversion direction. Assert known expected
  dates rather than deriving expectations with the algorithm under test.
- [ ] Cover both spring-forward and fall-back nights in America/New_York, including
  queries after the offset change but before noon. Add a narrow anchor assertion
  (a recording observer delegating to the real observer is sufficient) that the
  search uses the preceding date's actual local noon and `which="next"`; equal
  returned dates alone would miss an incorrectly offset anchor.
- [ ] Retain the equinox morning-calibration regression. Cover polar day and polar
  night, including pre-noon and midnight samples in a non-UTC zone; expect the
  query's local date for masked results. Capture only expected no-crossing warnings.
- [ ] Extend `tests/mixins/test_fitsheader.py` with sequential images carrying real
  `DATE-OBS` values across the reported sunset/midnight sequence. Use a real observer,
  the actual header and frame-number methods, a temporary VFS-backed YAML cache,
  and `format_filename()` with the default pattern. Assert constant `DAY-OBS`,
  consecutive `FRAMENUM`, persisted cache contents, and distinct filenames. Recreate
  the module against the same cache partway through to verify restart continuity;
  at next local noon assert one new date and a reset to 1. Do not prefill `DAY-OBS`
  or mock `night_obs()` in this regression. Keep existing disabled-night, missing-
  observer, missing-`DATE-OBS`, cache-error and uncached-counter coverage passing.
- [ ] Add focused caller checks for `Mastermind._next_obsnum()` across midnight
  with persistent cache and `DarkBiasScript._resolve_night()` at dawn with a real
  observer, retaining explicit-night precedence. Fix callers only if these reveal
  a separate necessary integration change; shared-helper correction should suffice.
- [ ] Demonstrate the new ordinary-night and local-date tests fail on the original
  implementation and pass with the fix. Run focused time, FITS, Mastermind and
  calibration tests, then the standalone suite (`uv run pytest tests`). Run CI's
  Ruff/pyrefly checks and Black on changed Python files. Record actual results and
  unavailable integration services separately; this plan does not mark tests run.

## Release and data handling

- [ ] Add a changelog entry describing corrected `DAY-OBS`, frame naming and
  observation numbering; recommend a prompt patch release after validation.
- [ ] Prefer deploying between observing runs. Correcting a previously wrong cached
  night during a run can itself reset the counter and reuse an existing corrected-
  date filename. Before resuming affected acquisition, preserve files and caches,
  inspect destination names and reconcile the counter with existing files under
  operator control. Do not automatically delete/reset caches or rename/re-ingest
  historical frames as part of this patch.
- [ ] Review affected nights for repeated filenames, mismatched headers and archive
  records using available logs/backups. The fix prevents this cause of future
  collisions; it cannot recover overwritten exposures or guarantee global filename
  uniqueness. Track any recovery or archive hardening separately.
- [ ] After merge, update this plan and its index with validation and release state;
  update fleet tracking if #995 is present, and distinguish release from deployment.
