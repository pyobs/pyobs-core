# FollowMerit: observing periods for nighttime and solar operation

Status: proposed — period policy and configuration ownership need agreement before implementation
Issue: [pyobs-core#967](https://github.com/pyobs/pyobs-core/issues/967)
Date: 2026-10-13

## Problem and evidence

`FollowMerit` asks for `data.night(time)`, the UTC date of the previous sunset.
`ObservationArchiveEvolution.observations_for_night()` instead fetches a UTC calendar day's
completed observations, using 00:00:00–23:59:59 overlap filters. MichaelJEvan reported that a
prerequisite completed after UTC midnight only became visible the following evening.

A local reproduction with a real astroplan observer (longitude −70°, latitude −30°, height
200 m) confirmed both errors. At October 13 03:00 UTC, sunset is approximately October 12
22:44 UTC. A completed `lights` observation at October 13 00:30–00:35 is missed, while one from
October 12 01:00 is accepted. The October 13 record incorrectly appears the following evening.

**Solar telescopes must also work:** their observing period can run from morning to evening.
A universal sunset-defined night is not the system's observing-period contract. The initial
sunset-to-next-sunset-only proposal is superseded by the choices below; do not implement it
without resolving daytime operation.

## Existing conventions and their limits

- `FileSystemObservationArchive._get_filename()` already has `mode="night"|"day"`: night
  mode keys by the **previous sunrise**, day mode by the **previous sunset**. These are history
  reset cycles in the normally inactive half of the day, not limits on when observations run.
- `PortalObservationArchive` accepts the same mode, but merely stores `_mode`; it never uses it
  to select history. There is no common archive-mode API to propagate into `DataProvider`.
- `OnDemandScheduler` stores `twilight`, but never uses it. Its solar-elevation constraints can
  permit daytime or nighttime operation. `AstroplanScheduler` does impose an astronomical or
  nautical `AtNightConstraint`; that separate scheduler is outside this fix.
- The solar IAGVT scheduler configuration (`../pyobs-iagvt/config/iagvtsrv/scheduler.yaml`)
  uses `OnDemandScheduler` and portal archives without an explicit day/night mode. Therefore
  existing solar deployments cannot be assumed to have selected `mode="day"` already.
- `PerNightMerit` counts completed task history since the previous sunrise, independently of
  `DataProvider.night()`. That matches the filesystem's **night** reset, but not its **day**
  reset. A sunrise reset also works within ordinary solar daylight, but differs for preparations
  before sunrise and follow-up work after sunset.

## Proposed semantics, with decisions to settle

Distinguish the **operating window** from the **history cycle**. Ordinary night operation runs
from evening to morning; solar operation runs from morning to evening. Existing task/global
constraints decide actual allowed hours, including twilight and calibration exceptions. History
membership must not silently prohibit those observations.

Prefer reusing the existing filesystem reset convention, subject to agreement:

| Mode | Typical operating window | Proposed history cycle |
|---|---|---|
| night | Sunset to following sunrise | Previous sunrise to next sunrise |
| day | Sunrise to following sunset | Previous sunset to next sunset |

Both cycles contain a full typical observing session without resetting at UTC midnight. A solar
morning prerequisite remains visible that afternoon; a nighttime prerequisite after UTC midnight
remains visible that night. The reset occurs in the opposite half-day. These are astronomical
event intervals, not fixed 24-hour durations or local calendar days.

**Decision required before code:** confirm this cycle convention versus strict operating windows
(night `[sunset, sunrise)`, day `[sunrise, sunset)`). Strict windows need explicit rules for
preparatory and follow-up calibrations and evaluations outside the window; this plan does not
silently discard those records. Under the proposed cycle convention, night history resets at
sunrise and day history at sunset: a post-sunrise night calibration cannot follow a pre-sunrise
prerequisite, and a post-sunset solar calibration cannot follow a daytime prerequisite. Confirm
these consequences against intended site workflows before accepting the convention.

**Configuration decision required:** choose one authoritative day/night setting and propagate it
to scheduler, provider, and evolution. Prefer existing `day`/`night` values and filesystem
semantics. A scheduler-owned setting would also support memory archives and standalone merits;
reusing an archive setting requires a common public interface and an explicit no-archive path.
Do not inspect private `_mode`, infer mode from target identity/constraints/twilight, or add a
general session framework for this bug. Specify a backward-compatible default and explicitly
configure solar callers as needed; there is no reliable automatic solar-site detection today.

**PerNightMerit decision required:** night mode can retain its current sunrise reset under the
proposal. In day mode, either make its limit use the same sunset-based cycle or explicitly retain
its sunrise-based meaning and document/test the difference outside daylight. Prefer a shared
cycle for consistent limits and prerequisites, but do not silently broaden this fix into a merit
behavior change. Record the selected option before implementing it.

For the chosen cycle/window, propose half-open membership `[opening, closing)` by **observation
start**, matching simulated `evolve()` assignment. A record crossing a reset belongs only to the
period where it started. This deliberately replaces today's inclusive overlap selection, which
can count a record in two periods. Keep task-ID matching, `COMPLETED` state, and FollowMerit's 0/1
result; no new completion-time/as-of history feature.

## Implementation checklist after those decisions

### 1. One period calculation for every caller

- [ ] Record the agreed period/reset, configuration owner, default, calibration-boundary rules,
  and PerNightMerit behavior above. Identify solar configurations needing an explicit setting;
  sibling configuration changes require a separately identified scope, not an implicit migration.
- [ ] Add one small shared period calculation used by `DataProvider`, archive fetching, and
  simulated membership. Avoid retaining `data.night()`'s sunset key for one path while fetching
  sunrise-based night history in another. Preserve a compatibility wrapper for existing public
  date-only calls, documenting the selected mode's date meaning.
- [ ] Carry the actual reference `Time` from scheduler prefetch and FollowMerit evaluation,
  plus `scheduled_task.start` for unfrozen `evolve()`. Derive opening and closing from the
  selected astronomical event(s), not date+noon, a UTC offset, or opening+24 hours. Validate
  key/reference agreement. Existing custom planners and direct merits must work without prefetch.
- [ ] If date-only compatibility reconstructs a period, locate the unique relevant event inside
  that UTC date using bounded candidate enumeration around midnight. Reject absent or ambiguous
  candidates explicitly; an anchor resolves ambiguity. Validate finite, unmasked and increasing
  events. Missing polar events fail before archive I/O; do not invent a polar calendar fallback.
- [ ] Define exact-event reference selection and half-open boundaries consistently across key
  calculation and filtering. Test astroplan's returned-event `previous`/`next` behavior; avoid
  a broad epsilon that shifts observations between periods. If a date alone is insufficient to
  identify a period, fail explicitly rather than silently reuse a cache bucket. A cache used for
  more than one mode must include mode in its key, or enforce one immutable mode per instance.

### 2. Archive membership and prefetch/freeze

- [ ] Query `COMPLETED` records with `start_after=opening`, `start_before=closing`, then filter
  locally to `opening <= obs.start < closing`. `ObservationList.filter()` and portal filters
  use inclusive `>=`/`<=` (`gte`/`lte`), so a strict local upper bound is necessary. Check supported
  memory/filesystem/LCO adapters preserve the opening-boundary record. No portal API change is
  needed merely to query these timestamps.
- [ ] Keep exactly one current-period fetch before freeze on the original event loop, plus
  task-history prefetch. Cache reads and frozen future-period seeding must do no archive I/O.
  Keep the missing-task error and missing-current/past-period canary. Resolve astronomy bounds
  only when necessary; no-archive empty results and frozen future misses need no live query.
- [ ] Assign synthetic completed observations using the **same selected period of their start**
  as real history. Replace every sunset-only scheduling/evolution call coherently. Keep one
  provider/evolution per schedule run and deterministic cache identity.
- [ ] Preserve the nonhistorical start-at-or-after-now invariant underlying empty future periods.
  If strict operating windows are chosen, resolve the inactive-gap case explicitly: prefetch
  must not mistake the previous completed session for the next empty one. Historical replay
  and executor redesign remain outside scope.

### 3. Tests and completion

- [ ] Use a filtering fake archive, not only empty mocks, to reproduce #967's missing current
  record, accepted previous record and delayed next-evening appearance. Test actual merit values,
  unrelated tasks and noncompleted records.
- [ ] Test night evening-to-morning and solar morning-to-evening sequences at western/eastern
  longitudes, including sessions crossing UTC midnight and events near UTC midnight. Test the
  selected history reset, not merely midnight, clears prerequisite eligibility on the next cycle.
- [ ] Cover solar morning prerequisite → afternoon follower, night post-midnight prerequisite →
  later-night follower, prior-session exclusion, and the agreed calibration boundary rules. Check
  PerNightMerit and FollowMerit together across sunrise/sunset according to the chosen policy.
- [ ] Cover opening inclusion, closing exclusion, straddling records, real/evolved parity, exact
  astronomical events, variable event-to-event durations, ambiguous/missing events and polar
  failures. Use deterministic boundary fixtures plus a few real-observer tests with offline IERS.
- [ ] Cover standalone merits and unfrozen evolve without prefetch, compatible date-only callers,
  no-archive paths, selected/default mode propagation and invalid/mismatched configuration.
- [ ] Exercise a full schedule across the selected reset: real prerequisite enables its follower,
  the next period begins empty, evolving a prerequisite enables its new follower. Assert the
  original archive thread/event loop and forbid any I/O after freeze, including worker evaluation.
- [ ] Run scheduler and relevant archive tests, Ruff, Black check, and pyrefly on changed Python
  files. Update affected mocks and fixtures to use real selected-period keys rather than UTC dates.
- [ ] Document the chosen semantics and any required solar configuration explicitly. Mark this
  plan implemented and update its index on landing; remove #967 and this plan from the fleet's
  open-items view when merged to `develop`.

Reference: [archive prefetch/freeze plan](2026-08-05-scheduler-archive-prefetch-for-process-isolation.md).
This remains a planning document only: no runtime/test implementation or external action.
