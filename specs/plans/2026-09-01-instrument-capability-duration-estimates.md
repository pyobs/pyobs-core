# Plan: Feed pyobs-portal instrument capability data into script duration estimates

Status: proposed (no issue filed yet; Repos: pyobs-core, pyobs-portal)

Follow-up to pyobs-portal#133 (`instruments` app: per-instrument camera/telescope/dome capability
data, incl. task-duration-estimate fields — readout time per binning, filter-change time, slew
rate, dome-rotate rate). That plan (`../../../pyobs-portal/specs/plans/2026-09-01-portal-instrument-config-app.md`)
deliberately scoped out consuming the data anywhere; this plan is where it gets consumed.

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

**1. `InstrumentCapabilities` models** (new: `pyobs/robotic/instruments.py`) — plain pydantic
models mirroring the shape `InstrumentSerializer` already emits (`pyobs_portal/instruments/serializers.py`):
`Instrument` (`module_name`, `cameras: list[CameraCapability]`, `telescope`, `dome`),
`CameraCapability` (`code`, `binnings: list[BinningOption]`, `filter_wheels: list[FilterWheelCapability]`,
...), `BinningOption` (`x`, `y`, `readout_time_s`), `FilterWheelCapability` (`filter_change_time_s`,
`filters: list[Filter]`), `TelescopeCapability` (`slew_rate_deg_per_s`, ...), `DomeCapability`
(`rotate_rate_deg_per_s`). No Django import — pyobs-core only ever deserializes the JSON the portal
API already returns. A small `InstrumentCapabilities` container wraps `dict[module_name, Instrument]`
plus a `camera(module_name) -> CameraCapability | None` / `by_camera_code(code) -> CameraCapability | None`
convenience lookup.

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
`self.telescope` (already-existing plain module-name string fields), and fall back to today's
constant whenever the lookup misses at any level (no `data`, no `instrument_capabilities`, no
matching `Instrument`, or the specific field is `None` on the matched row):

| Script | Looks up | Replaces |
| --- | --- | --- |
| `ImagingScript` | camera's matching `BinningOption.readout_time_s`, active filter wheel's `filter_change_time_s`, telescope's `slew_rate_deg_per_s` | adds readout + filter-change (currently absent), replaces the `60.0`/`30.0` fudge |
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
  (no "current pointing" state at estimate time) — first pass uses a fixed placeholder distance;
  a real fix (e.g. estimating from the target's actual sky position vs. last-known pointing) is
  future work.

## Test plan

- [ ] pyobs-core: `InstrumentCapabilities` model round-trips the portal's actual
      `InstrumentSerializer` JSON shape (fixture from pyobs-portal's own test data)
- [ ] pyobs-core: each of the 5 leaf scripts' `estimate_duration()` — with capability data present
      (correct math) and absent/partial (falls back to today's constant, unchanged)
- [ ] pyobs-core: `PortalTaskArchive` instrument-capability fetch — marker-gated refresh, and
      degrades to last-good cache (not `None`, not raise) on a fetch failure
- [ ] pyobs-core: `OnDemandScheduler`'s 4 call sites forward `instrument_capabilities` correctly;
      `AstroplanScheduler` unaffected (still reads `task.duration`)
- [ ] pyobs-portal: `last_instrument_update/` reflects nested capability edits, not just
      `Instrument`-row edits
- [ ] pyobs-portal: `estimate_duration/` returns different durations with vs. without a matching
      `Instrument` row for the task's `camera`/`telescope`, cache TTL respected
- [ ] Manual: script builder duration estimate visibly changes after editing an instrument's
      capability data in the admin
