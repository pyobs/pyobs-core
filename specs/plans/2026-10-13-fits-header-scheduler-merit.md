# Keep the scheduler's merit on the observation and write it into the FITS header

Status: core part implemented (2026-10-13, PR in pyobs-core), portal part in a pyobs-portal PR.

Repos: pyobs-core, pyobs-portal

## Context

#962 part 8: "the value the scheduler ranked the slot by. This needs the portal to keep the
observation's `priority`, so the mastermind can read it back at run time." Parts 6 and 7 are in
`2026-10-13-fits-header-constraints-and-priorities.md`; this plan adds `HIERARCH REQ MERIT` to the
same place. Checked against pyobs-core `develop` (`93876735`) and pyobs-portal `develop`
(`6e2f6bc`, local checkout, not fetched). Marks: **[code]** read from code, **[inferred]** follows
from code but not tested, **[unverified]** not checked.

### pyobs-core today

- **[code]** `Observation.priority: float | None = None` (`pyobs/robotic/observation.py:36`).
  The field exists in v2.0.0 and v2.14.2 as well (checked with `git show`). `Observation` is a
  `BaseModel` with `extra="forbid"` (`pyobs/utils/serialization.py:28`).
- **[code]** `OnDemandScheduler` multiplies the merit by task priority and project priority
  (`pyobs/robotic/scheduler/ondemandscheduler.py:296-302`) and stores the product as
  `priority=merit` in `create_scheduled_task` (`ondemandscheduler.py:199-210`). So the stored value
  is the ranking value (merit times priorities), evaluated for the slot's planned start.
- **[code]** `AstroplanScheduler` does not set `Observation.priority` (`astroplanscheduler.py:231`).
  Its own `1000 - task.priority` (`astroplanscheduler.py:123-131`) is an astroplan block priority
  with the opposite meaning and is not stored.
- **[code]** `PortalObservationArchive` sends the full model with `model_dump(use_task_id=True)`,
  which includes `priority`, both on `add_observations` (POST, `portal/observationarchive.py:144-156`)
  and `update_observation` (PUT, `portal/observationarchive.py:253-265`).
- **[code]** The scheduler module replaces the plan on each reschedule: `clear_schedule(start)` and
  `add_observations(...)` (`pyobs/modules/robotic/scheduler.py:340,366,378`). Each pending row
  therefore carries the merit from the plan that created it.
- **[code]** The mastermind takes `observation` from `get_next_observation` (`mastermind.py:205-207`),
  keeps only `self._task`, `self._task_target` and `self._obsnum` (`mastermind.py:260-262`), and
  PUTs the observation on start, failure and finish (`mastermind.py:278` and later).
- **[code]** Other archives: `MemoryObservationArchive` keeps the objects, so `priority` survives.
  The filesystem archive dumps with `exclude_defaults=True`
  (`filesystem/observationarchive.py:257`), so a non-`None` priority is kept. The LCO archive maps
  nothing into `Observation.priority` (`LcoObservation.priority` in `lco/_portal.py:151` is LCO's
  own integer); it stays `None`.

### pyobs-portal today

- **[code]** The `Observation` model has no priority column: fields `task`, `start`, `end`,
  `state`, `target`, `obsnum`, `updated_at` (`pyobs_portal/api/models.py:82-98`).
- **[code]** `ObservationSerializer` lists `id`, `task`, `start`, `end`, `state`, `target`,
  `obsnum`, `archive_url` (`pyobs_portal/api/serializers.py:84-98`). **[inferred]** DRF's
  `ModelSerializer` ignores input keys that are not declared fields, so the `priority` that every
  2.x core already sends is dropped today without an error.
- **[code]** Views: `ObservationList` (`views.py:126`, list POST via `get_serializer(many=True)` at
  `views.py:143-146`) and `ObservationDetail` (`views.py:150`, retrieve/update).
- **[code]** Last migration: `0009_project_updated_at.py`.
- **[code]** API docs: `docs/source/api.rst:25-27` (observations). They say `PATCH`, core uses
  `PUT` (`RetrieveUpdateAPIView` allows both).
- **[code]** Specs: `specs/plans/` with `specs/index.md`; the portal's `CLAUDE.md` points to
  pyobs-core's cross-repo convention.

## What is stored, and when it can differ from run time

`REQ MERIT` is a **plan-time snapshot**: the product merit times task priority times project
priority that the scheduler computed for the slot's planned start, when it created that observation
row. It can differ from a value computed at run time because:

- the task starts later than planned (up to `allowed_late_start`, default 300 s), and merits that
  depend on time (e.g. airmass) have changed;
- task or project priority was edited after planning. **[inferred]** An edit moves the portal's
  task marker and usually triggers a reschedule, which replaces pending rows, but a row already
  running keeps its value;
- a custom planner (as in #962) may store a different quantity, or nothing.

The docs and the card comment must say "plan-time ranking value", not "merit".

## Mixed versions

| | Old core (any 2.x) | New core |
|---|---|---|
| **Old portal** | today | core sends `priority`, portal drops it; GET has no `priority`, core sees `None`, no `REQ MERIT` card |
| **New portal** | core already sends `priority` (since 2.0), portal stores it; GET returns it, 2.x `Observation` has the field, so `extra="forbid"` accepts it; old mastermind writes no card | full feature |

**[inferred]** No combination breaks. Cores older than 2.0 are out of scope.

## Proposed changes

### pyobs-portal (PR in pyobs-portal)

- [ ] `Observation.priority = models.FloatField(null=True, blank=True)` in `api/models.py`.
- [ ] Migration `0010_observation_priority.py` (nullable, no data migration; existing rows stay
      `NULL`).
- [ ] Add `"priority"` to `ObservationSerializer.Meta.fields`, read-write.
- [ ] `docs/source/api.rst`: mention `priority` on observations ("the scheduler's ranking value
      for this slot at planning time, may be null").
- [ ] Portal `specs/index.md`: an entry referencing this plan in pyobs-core, as required by the
      cross-repo convention. Not created by this plan; done in the portal PR.
- [ ] Frontend display: out of scope (Open question 3).

### pyobs-core (PR in pyobs-core, after or with plan 1)

- [ ] `Mastermind`: keep `self._observation: Observation | None`, set next to `self._task`
      (`mastermind.py:260`), cleared wherever `self._task` is cleared (`mastermind.py:298,314`).
- [ ] In `get_fits_header_before`: if `self._observation.priority is not None`, write
      `HIERARCH REQ MERIT` as `float`, comment empty or `"plan-time rank"`.
- [ ] No change to `Observation`, the archives or the schedulers.
- [ ] Docs: add `REQ MERIT` to the "FITS headers of a robotic run" section from plan 1, with the
      plan-time meaning, and a note that only schedulers that set `Observation.priority` (today
      `OnDemandScheduler`, not `AstroplanScheduler`) produce it, so custom planners must set it.
- [ ] Changelog entry at release.

### Release order

Portal first: it starts storing the value that every 2.x core already sends, so data accumulates
before the core release. Then core. Either order works (see the matrix), so this is a preference,
not a requirement.

## Tests

### pyobs-portal (`pyobs_portal/api/tests.py`, `uv run python manage.py test`)

- [ ] POST a list of observations with `priority` set: stored and returned by GET.
- [ ] POST without `priority`: stored as `NULL`, GET returns `null`.
- [ ] PUT an observation with the same `priority` and a new `state`: priority unchanged.
- [ ] Migration applies on a database with existing observations (rows get `NULL`).

### pyobs-core (no server)

- [ ] `tests/modules/robotic/test_mastermind.py`: with `_task` and `_observation` set and
      `priority=2.5`: `HIERARCH REQ MERIT` is 2.5; with `priority=None`: no card; after a finished
      and after a failed run, `_observation` is `None`.
- [ ] `tests/robotic/storage/portal/`: `model_dump(use_task_id=True)` of an observation contains
      `priority` (guards the wire field the portal now stores), and an observation payload from the
      portal with `priority` validates.
- [ ] `OnDemandScheduler`: the created observation's `priority` equals merit times task priority
      times project priority. `tests/robotic/scheduler/test_ondemandscheduler.py` has no
      `priority` assertion today, so add one there. Portal archive tests go in
      `tests/robotic/storage/portal/test_portal_archives.py`.

## Decisions

Tim's naming decisions from plan 1 apply (`HIERARCH REQ MERIT`, written by the mastermind). No new
decision with a rejected alternative here, so no ADR.

## Open questions

1. **Name the stored value `merit` instead of `priority` on the portal?** Recommend keep
   `priority`: core already sends that key from every 2.x version, so the portal stores it for old
   cores without any core change. Document the meaning instead.
2. **Store the merit without priorities as well?** Recommend no for now: #962 asks for the value
   the slot was ranked by, and task/project priorities are written as their own cards (plan 1), so
   the plain merit can be computed from the three.
3. **Show `priority` in the portal's Observations tab?** Recommend later, separate issue.
4. **Should `AstroplanScheduler` set `Observation.priority`?** Recommend no: its ranking is
   astroplan's internal one with a different meaning, and a mixed meaning in one column would make
   the dataset misleading.

## Not verified

- DRF ignoring the undeclared `priority` input key today (standard `ModelSerializer` behaviour, not
  tested against this portal).
- Whether the portal's local checkout is behind `origin/develop` (not fetched).
- Whether the reporter's planner sets `Observation.priority`.
- Whether an edit to a task or project always triggers a reschedule in the reporter's setup
  (depends on scheduler triggers, `scheduler.py:139-141`).

## Out of scope

- Constraint and priority cards (plan 1).
- LCO: mapping `LcoObservation.priority` into `Observation.priority`.
- Showing the merit in the portal frontend.
