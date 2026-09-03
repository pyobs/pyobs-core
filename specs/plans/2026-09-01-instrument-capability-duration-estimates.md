# Plan: Feed pyobs-portal instrument capability data into script duration estimates

Status: implemented, closed 2026-09-03 (Repos: pyobs-core, pyobs-portal)

Follow-up to pyobs-portal#133 (merged 2026-09-01/02; `instruments` app: per-instrument
camera/telescope/dome capability data, incl. task-duration-estimate fields — readout time per
binning, filter-change time, slew rate, dome-rotate rate). That plan
(`../../../pyobs-portal/specs/plans/2026-09-01-portal-instrument-config-app.md`) deliberately
scoped out consuming the data anywhere; this plan is where it gets consumed.

Was blocked on pyobs-portal#139 (as merged, `Instrument.module_name` conflated the grouping's
identity with the telescope's module name, and `CameraCapability` had no module-name field at all
— only `code`, a different, physical-hardware-ID namespace — so there was no key to look up a
camera capability by `ImagingScript.camera`/`DarkBiasScript.camera` etc.). Landed 2026-09-02 in
pyobs-portal#140: `module_name` now lives on each device-capability model (`TelescopeCapability`,
`DomeCapability`, `CameraCapability`) and `InstrumentDetail` is dropped — the design below
(§A.1/§A.8) already assumes that flatter shape, no further changes needed there before starting
implementation.

Filed as a review follow-up on #140 (not a separate blocker — `FilterWheelCapability` was the one
device-capability model the #139/#140 flattening left out, so there was still no `module_name` key
to resolve "which filter wheel" for `ImagingScript`'s filter-change estimate). Landed 2026-09-02 in
pyobs-portal#142: `FilterWheelCapability.module_name` (nullable — a wheel isn't always its own
addressable module). §A.1/§A.8 below already assume it.

§B's implementation detail (cache helper, `last_instrument_update/` marker, `schema.py` wiring)
now has its own plan on the pyobs-portal side:
`../../../pyobs-portal/specs/plans/2026-09-02-instrument-capability-estimate-duration-endpoint.md`
— written against the `instruments` app as actually implemented post-#140 (confirmed
`GET /api/instruments/` already exists with `INSTRUMENT_QUERYSET`'s prefetch shape; `schema.py`'s
`estimate_duration()` is currently at `:766-792`, not `:748-774` as first estimated below). §B
below is kept for cross-repo context but that doc is the current source of truth for the
pyobs-portal-side design.

**Fully landed 2026-09-03.** §A shipped across four PRs — models (pyobs-core#864), `TaskData`/
`TaskArchive`/scheduler plumbing (pyobs-core#865), the 5 leaf scripts (pyobs-core#867, minus
`SelectorScript` per Non-goals), and `PortalTaskArchive`'s marker-gated poll (pyobs-core#868) —
and released to PyPI as pyobs-core v2.4.0. §B shipped in pyobs-portal#144 (marker endpoint, cache
helper, `schema.py` wiring, feature-detected against a pyobs-core release that might predate
pyobs-core#864) and pyobs-portal#145 (bumped this repo's pin to v2.4.0, confirmed
`HAS_INSTRUMENT_CAPABILITIES` now `True` and the previously-skipped test exercising for real,
148/148 passing against the actual PyPI release). Real capability data now reaches both the
script builder's live auto-estimate and `OnDemandScheduler` end-to-end, pending pyobs-portal's
own `develop`→`main` release/deploy (tracked separately, not part of this plan).

## Problem

Several `Script.estimate_duration()` implementations in pyobs-core return hardcoded fudge
constants, most with an explicit `# TODO` admitting it:

| Script | Location | Current estimate | Missing |
| --- | --- | --- | --- |
| `ImagingScript` | `pyobs/robotic/scripts/imaging/imaging.py:354-368` | `sum(exposure_time * count) * repeats + 60.0` (+30.0 if acquisition) | readout time, filter-change time, slew time — none counted at all |
| `PointingScript` | `pyobs/robotic/scripts/calibration/pointing.py:52-55` | flat `60.0` | slew time |
| `DarkBiasScript` | `pyobs/robotic/scripts/calibration/darkbias.py:277-288` | flat `readout = 5.0` per frame | real per-binning readout time |
| `AutoFocusScript` | `pyobs/robotic/scripts/imaging/autofocus.py:91-93` | `count * exposure_time + 60.0` | slew time |
| `SelectorScript` | `pyobs/robotic/scripts/control/selector.py:53-55` | flat `30.0` | real mode-change time (uncertain fit — see Non-goals) |

`ImagingScript` is the highest-value target: it currently adds *no* readout or filter-change
overhead at all, not even a fudge constant, despite `configuration.instrument_configs` often
implying both.

This directly affects two consumers of duration estimates:
- **pyobs-portal's script builder** (`pyobs_portal/api/schema.py:748`, `estimate_duration/`
  endpoint) — fires on every script edit (issue #96's auto-estimate), shown live to the user
  composing a script.
- **`OnDemandScheduler`** (`pyobs/robotic/scheduler/ondemandscheduler.py:168,233,285,304`) — calls
  `task.estimate_duration(time=...)` live, at four call sites, to place tasks in a schedule.
  (`AstroplanScheduler` does *not* call `estimate_duration()` — see Non-goals.)

## Existing conventions this follows

- **Bulk-fetch-once + in-memory cache + poll-a-cheap-marker**, not per-item queries — this is
  already how `PortalTaskArchive` (`pyobs/robotic/storage/portal/taskarchive.py`) handles
  tasks/projects: `_check_for_changes()` polls `last_task_update/` (a DB-derived `Max(updated_at)`
  marker, pyobs-portal#84) and only re-downloads on a marker move. New instrument-capability
  fetching mirrors this rather than querying per-script or per-task.
- **`TaskData` as the context bag threaded through `estimate_duration()`** — every control-flow
  wrapper (`sequential.py`, `parallel.py`, `cases.py`, `conditional.py`) already forwards `data:
  TaskData` unchanged to sub-scripts' `estimate_duration()`. `transitimaging.py:91-105` already
  pulls a `TransitMerit` out of `data` this way, with a None-safe fallback
  (`super().estimate_duration(...)`) when it's missing. `instrument_capabilities` is a new field
  on `TaskData`, not a new parameter threaded through every script.
- **Plain module-name strings as the identity key**, never a DB FK — `Instrument.module_name` in
  pyobs-portal#133 is deliberately the same free-text convention as `ImagingScript.camera`/
  `.telescope` (`imaging.py:108-109`) and `2026-08-24-module-ref-dropdowns.md`'s
  `GET /api/modules/classes/`. Capability lookup keys off this string, no new identity scheme.
- **Optional/degrade-to-None everywhere**, never raise — `pyobs_portal/api/webadmin.py`'s
  `get_module_classes()` is the precedent: a missing/unreachable external source returns `None`
  and callers fall back to today's behavior, never an error surfaced to the user. Same shape here:
  no `instruments` app entry, an unreachable portal, or a stale cache all resolve to `None` and
  every consuming script keeps its current constant.
- **`django.core.cache` with a short TTL**, same idiom as `webadmin.py:23-25,47-70`
  (`_CACHE_KEY`/`_CACHE_TTL`/`_UNCACHED` sentinel, `cache.get`/`cache.set`) — reused for the
  portal-side cache below, just ORM-backed instead of an HTTP call since `instruments` lives in
  the same Django process as `schema.py`.

## Design

### A. pyobs-core

**1. `InstrumentCapabilities` models** — **landed 2026-09-02 in pyobs-core#864.** (new: `pyobs/robotic/instruments.py`) — plain pydantic
models mirroring the shape `InstrumentSerializer` already emits (`pyobs_portal/instruments/serializers.py`),
post-#139: `Instrument` (`display_name`, `notes`, `cameras: list[CameraCapability]`, `telescope`,
`dome` — no `module_name` of its own), `CameraCapability` (`module_name`, `code`,
`binnings: list[BinningOption]`, `filter_wheels: list[FilterWheelCapability]`, ...),
`BinningOption` (`x`, `y`, `readout_time_s`), `FilterWheelCapability` (`module_name`,
`filter_change_time_s`, `filters: list[Filter]` — `module_name` nullable, per pyobs-portal#142:
not every wheel is its own addressable module), `TelescopeCapability` (`module_name`, `slew_rate_deg_per_s`, ...),
`DomeCapability` (`module_name`, `rotate_rate_deg_per_s`). No Django import — pyobs-core only ever
deserializes the JSON the portal API already returns.

`InstrumentCapabilities` flattens the nested response into module-name-keyed dicts built once at
parse time — `dict[module_name, CameraCapability]`, `dict[module_name, TelescopeCapability]`,
`dict[module_name, DomeCapability]`, `dict[module_name, FilterWheelCapability]` (skipping rows
with a `None` `module_name`) — with `camera(module_name)`/`telescope(module_name)`/
`dome(module_name)`/`filter_wheel(module_name)` lookups hitting those directly (each script only
ever needs one device's capability row, never "the instrument" as a concept) plus
`by_camera_code(code) -> CameraCapability | None` for the fleet-wide-ID case. No two-step "resolve
`Instrument`, then search its nested list" indirection — `self.camera`/`self.telescope`/
`self.filters` (already-existing plain module-name string fields on the scripts) match directly
against a leaf capability's own `module_name`.

**2. `TaskData` gains a field** (`pyobs/robotic/task.py:24-34`):
```python
class TaskData:
    task: Task
    observation_archive: ObservationArchive | None = None
    task_archive: TaskArchive | None = None
    target: Target | None = None
    instrument_capabilities: InstrumentCapabilities | None = None
```

**3. `TaskArchive` gains a new method**, default `None` (`pyobs/robotic/storage/taskarchive.py`):
```python
def get_instrument_capabilities(self) -> InstrumentCapabilities | None:
    return None
```
Every non-portal backend (filesystem, memory, lco) inherits the `None` default unchanged — this
data only ever exists for the portal backend, consistent with "optional everywhere."

**4. `PortalTaskArchive` overrides it**, fetching/caching the same way it already handles
tasks/projects: a background poll (folded into the existing `_check_for_changes` loop, or a
sibling coroutine on the same cadence) gated on a new portal marker endpoint (§B.1), downloading
`GET /api/instruments/` only when the marker moves, caching the parsed `InstrumentCapabilities` in
memory. On a fetch failure, keep serving the last-good cache (same as the existing
`_poll_error_throttle` pattern at `taskarchive.py:34-36,63-69`) rather than clearing it.

Two things pyobs-core#864's review flagged as needing a decision here, not before (§A.1's field
sets match the portal's current payload exactly, so neither is a problem yet):
- **`extra="forbid"` on the §A.1 models degrade-to-`None` conflict.** They inherit
  `pyobs.utils.serialization.BaseModel`'s `extra="forbid"`, so a portal field addition/rename (a
  real risk — #139/#140/#142 just reshaped this exact payload three times) raises `ValidationError`
  for the *whole* response, not just the new field. Under this section's "fetch failure keeps
  last-good cache" design, a `ValidationError` needs to be caught and treated as a fetch failure
  here (or the §A.1 models switched to `extra="ignore"`) — otherwise a first-ever parse failure
  (before any cache exists) leaves `instrument_capabilities` permanently `None` instead of
  degrading gracefully once the portal payload drifts.
- **Pagination truncation.** `GET /api/instruments/` is DRF-paginated (`PAGE_SIZE=100` in portal
  settings) and `InstrumentCapabilities.from_api_response()` expects the caller to hand it an
  already-unwrapped `results` list — fine today, but this fetch needs to either page through all
  results or the portal view needs `pagination_class = None`, or a fleet with >100 instruments
  silently loses coverage past the first page.

**5. `Task.estimate_duration()` gains an optional parameter** (`pyobs/robotic/task.py:121-123`):
```python
def estimate_duration(self, time: Time | None = None, instrument_capabilities: InstrumentCapabilities | None = None) -> float:
    if self.script:
        return self.create_script().estimate_duration(TaskData(task=self, instrument_capabilities=instrument_capabilities), time)
    return self.duration
```

**6. `TaskScheduler.schedule()` threads it through** (`pyobs/robotic/scheduler/taskscheduler.py:20-27`):
add `instrument_capabilities: InstrumentCapabilities | None = None` to the abstract signature.
`OnDemandScheduler` forwards it into all four `task.estimate_duration(time=...)` call sites
(`ondemandscheduler.py:168,233,285,304`). `AstroplanScheduler` accepts the parameter (interface
consistency) but doesn't use it — see Non-goals.

**7. The caller supplies it**: `pyobs/modules/robotic/scheduler.py`, which already holds
`self._task_archive` (line 108) and calls `self._scheduler.schedule(self._tasks, self._projects,
start, end)` (line 288), passes `self._task_archive.get_instrument_capabilities()` as the new
argument. No other caller of `schedule()` needs changes — this is the only place it's invoked
outside tests.

**8. The five leaf scripts** read `data.instrument_capabilities`, look up by `self.camera`/
`self.telescope`/`self.filters` (already-existing plain module-name string fields), and fall back
to today's constant whenever the lookup misses at any level (no `data`, no
`instrument_capabilities`, no `CameraCapability`/`TelescopeCapability`/`FilterWheelCapability` row
with that `module_name`, or the specific field is `None` on the matched row):

| Script | Looks up | Replaces |
| --- | --- | --- |
| `ImagingScript` | camera's matching `BinningOption.readout_time_s`, `self.filters`-matched `FilterWheelCapability.filter_change_time_s` (pyobs-portal#142 gave `FilterWheelCapability` its own `module_name`, so this matches directly like camera/telescope rather than needing an "active wheel" heuristic — falls back to today's constant if `self.filters` is unset or the wheel's `module_name` is `None`/unmatched), telescope's `slew_rate_deg_per_s` | adds readout + filter-change (currently absent), replaces the `60.0`/`30.0` fudge |
| `PointingScript` | telescope's `slew_rate_deg_per_s` | flat `60.0` |
| `DarkBiasScript` | camera's matching `BinningOption.readout_time_s` | flat `readout = 5.0` |
| `AutoFocusScript` | telescope's `slew_rate_deg_per_s` | the `+60.0` slew fudge |
| `SelectorScript` | — (see Non-goals) | flat `30.0`, likely unchanged |

Slew/rotate *rate* alone isn't a duration — these scripts need a distance to slew/rotate, which
none currently track (no "current pointing" concept at plan-estimate time). First pass: use a
fixed representative distance (e.g. a configured or hardcoded "typical slew" degrees figure) times
the real rate, which is still a better estimate than a flat constant untied to the actual
telescope. Flag this as a simplification worth revisiting, not a blocker.

### B. pyobs-portal

**1. New endpoint** `last_instrument_update/` (`pyobs_portal/instruments/urls.py` +
`pyobs_portal/instruments/views.py`), mirroring `last_task_update`
(`pyobs_portal/api/views.py:301-303`): `Max(updated_at)` across `Instrument` and its nested
capability rows (each already carries its own `updated_at` per the PR133 design doc's caveat that
Django admin doesn't bubble nested-inline edits up to the parent's `updated_at`).

**2. New cache helper**, `pyobs_portal/api/instrument_capabilities.py`, same shape as
`webadmin.py`'s `get_module_classes()` but ORM-backed instead of `requests.get`:
```python
_CACHE_KEY = "pyobs_portal.api.instrument_capabilities.all"
_CACHE_TTL = 300  # seconds — admin-edited reference data, staleness is cheap
_UNCACHED = object()

def get_instrument_capabilities() -> dict[str, Any] | None:
    cached = cache.get(_CACHE_KEY, _UNCACHED)
    if cached is not _UNCACHED:
        return cached
    data = InstrumentSerializer(INSTRUMENT_QUERYSET, many=True).data
    cache.set(_CACHE_KEY, data, _CACHE_TTL)
    return data
```
No HTTP round-trip — `instruments` lives in the same process/DB as `schema.py`, so this is a
cached ORM query, not a cached external call. TTL-based rather than marker-gated (unlike §A.4):
simpler, and acceptable here since this cache only serves the portal's own in-process callers,
not something the pyobs-core scheduler polls.

**3. `schema.py:748-774`'s `estimate_duration()` populates the new `TaskData` field**:
```python
return {"duration": script.estimate_duration(
    data=TaskData(task=task, instrument_capabilities=get_instrument_capabilities()),
    time=None,
)}
```

## Non-goals / open questions

- **`AstroplanScheduler` keeps reading the stored `task.duration` field**
  (`astroplanscheduler.py:114`), not a live `estimate_duration()` call — it never called
  `estimate_duration()` before this plan and this plan doesn't change that. It benefits
  indirectly, for free, once the portal-side `estimate_duration/` endpoint (which *does* now use
  real capability data) is what populates the stored `duration` on save — but making
  `AstroplanScheduler` itself call `estimate_duration()` live would be a separate, bigger behavior
  change (re-estimating on every scheduling pass instead of trusting a stored value) and isn't
  part of this plan.
- **`SelectorScript`'s mode-change duration** — unclear which capability field, if any, actually
  applies (a "mode change" isn't necessarily a filter change). Likely ships this pass with no
  lookup wired up, keeping its flat `30.0`, pending a look at what `SelectorScript` modes are
  actually used for in practice.
- **Live reconciliation against `ICamera`/`IBinning`/etc. stays explicitly out of scope**, per
  pyobs-portal#133's own scoping — this plan only ever reads the portal's hand-entered planning
  data, never queries a live module.
- **Representative slew/rotate distance** for `ImagingScript`/`PointingScript`/`AutoFocusScript`
  (no "current pointing" state at estimate time) — first pass uses a fixed placeholder distance.
  A real distance needs both a destination and a start position; the destination is trivial
  (`task.target`/`TaskData.resolved_target` already has RA/Dec), but the start position splits
  into three cases of very different difficulty:
  - **`OnDemandScheduler`'s first placed task in a `schedule()` call**: solvable now, cheaply — one
    async `IPointingRaDec`/`IPointingAltAz` proxy call to the live telescope before `schedule()`
    runs, threaded through the same way this plan already threads `instrument_capabilities` (fetched
    once by `pyobs/modules/robotic/scheduler.py`, passed into `TaskScheduler.schedule()`/`TaskData`).
    `estimate_duration()` itself is sync so can't make the live call directly — it must be
    pre-fetched by the caller.
  - **Every task after the first in the same scheduling pass**: not currently possible without new
    scheduler state. `OnDemandScheduler`'s greedy generator (`schedule_in_interval` →
    `schedule_first_in_interval` → recursion, `ondemandscheduler.py`) doesn't track "last scheduled
    task's target" across calls — `create_scheduled_task` builds each `Observation` independent of
    what came before. Would need that state threaded through the recursion, plus care around
    `check_for_better_task`/`can_postpone_task`'s speculative/out-of-order scheduling (tasks can be
    yielded out of the order they were evaluated in) — tracked as pyobs-core#859.
  - **pyobs-portal's script-builder live-edit estimate**: no concept of "previous task" or a live
    telescope exists there at all — it's an isolated single-script edit in the Django process
    (`schema.py`'s `estimate_duration()`), not part of a schedule.

  First pass (this plan) ships the fixed-placeholder version for all three cases. The first two
  cases above are real future work worth their own issues, not just "future work" hand-waving — see
  pyobs-core#858 (first task) and pyobs-core#859 (every task after). The portal-UI case needs more
  design first before it's even issue-shaped.

## Test plan

- [x] pyobs-core: `InstrumentCapabilities` model round-trips the portal's actual
      `InstrumentSerializer` JSON shape (fixture from pyobs-portal's own test data) — pyobs-core#864
- [x] pyobs-core: each of the 5 leaf scripts' `estimate_duration()` — with capability data present
      (correct math) and absent/partial (falls back to today's constant, unchanged) — pyobs-core#867
- [x] pyobs-core: `PortalTaskArchive` instrument-capability fetch — marker-gated refresh, and
      degrades to last-good cache (not `None`, not raise) on a fetch failure — pyobs-core#868
- [x] pyobs-core: `OnDemandScheduler`'s 4 call sites forward `instrument_capabilities` correctly;
      `AstroplanScheduler` unaffected (still reads `task.duration`) — pyobs-core#865
- [x] pyobs-portal: `last_instrument_update/` reflects nested capability edits, not just
      `Instrument`-row edits — pyobs-portal#144
- [x] pyobs-portal: `estimate_duration/` returns different durations with vs. without a matching
      `Instrument` row for the task's `camera`/`telescope`, cache TTL respected — pyobs-portal#144
- [ ] Manual: script builder duration estimate visibly changes after editing an instrument's
      capability data in the admin — not yet clicked through by hand; automated coverage above
      (pyobs-portal#144's `EstimateDurationInstrumentCapabilitiesTests`, real path, 0 skipped as of
      pyobs-portal#145) exercises the same code path, but nobody has watched it in a browser yet
