# Plan: Make the pydantic config layer reject unknown keys (`extra="forbid"`)

Status: implemented

Related: `specs/plans/2026-08-09-object-kwarg-validation.md` — the sibling plan for the *other*
silent-drop layer (`Object.__init__` swallowing leftover `**kwargs`). This plan is the pydantic
counterpart. The two are complementary, not redundant: a typo'd key on a pydantic model is dropped
by pydantic, never reaches `Object.__init__`, so fixing one does not fix the other.

## Problem

Every config-driven pydantic model in pyobs-core inherits `pyobs.utils.serialization.BaseModel`,
whose `model_config` is `ConfigDict(arbitrary_types_allowed=True)` with no `extra` override
(`pyobs/utils/serialization.py:28`). pydantic v2 defaults to `extra="ignore"`, so any key in a
config that the model does not declare is silently dropped. No warning, no error.

This bit us directly: a task YAML put `guiding_config` and `acquisition_config` inside
`instrument_configs`, but those fields belong on `ImagingScript.Configuration`, not on
`InstrumentConfig` (`pyobs/robotic/scripts/imaging/imaging.py:48-66`). pydantic dropped both, the
`Configuration`-level defaults (`enabled=True`) applied instead of the requested `enabled=false`,
and the task then failed `can_run` forever waiting on an acquisition module and autoguider that
were never configured. The task was scheduled but never executed, with no error pointing at the
config.

## Decision

Set `extra="forbid"` **globally** on `BaseModel` and `PolymorphicBaseModel`. Breaking existing
configs is accepted. A hard failure at load time is the point: a misspelled or misplaced key should
never again silently produce a task that does the wrong thing.

## Gap: the imaging config models are not covered by this change

The bug this plan is named after is in `pyobs/robotic/scripts/imaging/imaging.py:7`, which imports
`BaseModel` from pydantic directly, not from `pyobs.utils.serialization`. `AcquisitionConfig`,
`GuidingConfig`, `InstrumentConfig`, and `Configuration` are therefore plain pydantic models with
`extra="ignore"`, and the misplaced `guiding_config`/`acquisition_config` keys are still dropped
after this plan lands. Verified at runtime: `InstrumentConfig` is not a `pyobs` `BaseModel` subclass
and its `extra` is unset. These four models must get `extra="forbid"` too (directly, or by
inheriting `pyobs.utils.serialization.BaseModel`), or the regression test in the checklist below
cannot raise. `object.py:24` and `config_schema.py:10` also import pydantic `BaseModel`, but only
for `issubclass` checks, so they are unaffected.

## What breaks, and how to fix each

Empirically confirmed by flipping `extra="forbid"` on `BaseModel` and running the full test suite
(`.venv/bin/pytest`). Three breakage classes, all now understood:

1. **LCO portal payloads — reclassified, see below.** `pyobs/robotic/storage/lco/_portal.py`
   declares pydantic models that parse responses from the LCO Observation Portal. Originally this
   plan treated that portal as an external, unversioned third-party API and proposed opting the
   model family out with `extra="ignore"`. That premise was wrong: it's LCO's original portal
   software, but **self-hosted on our own server** — we control the upgrade cadence. That makes it
   the same kind of boundary as everything else this plan wants strict: a schema mismatch should be
   a loud failure at the moment we choose to upgrade the portal, not a silent drop that surfaces
   later as a mystery bug. Decision: **declare the missing fields, use `forbid` here too, no
   carve-out.**

   Failing tests: `tests/robotic/storage/lco/test_lco_http.py`, `test_task.py`, `test_portal.py`,
   `test_schedulereader.py`, `test_schedulewriter.py`, `test_lcotask.py`.

   Missing fields, enumerated by flipping `extra="forbid"` in an isolated worktree and running the
   full suite (field names/types cross-checked against `tests/robotic/storage/lco/conftest.py`
   fixtures — types below are inferred from fixture values, confirm against a live portal response
   before finalizing):
   - `LcoSchedulableRequest`: `state: str`, `submitter: str`
   - `LcoConfiguration`: `instrument_name: str = ""`, `guide_camera_name: str = ""`,
     `summary: ConfigurationSummary = Field(default_factory=ConfigurationSummary)` — these three
     only appear when a `LcoConfiguration` is embedded in a schedule-download response
     (`LcoObservation.request.configurations[*]`), not in the schedulable-request context, so they
     need to be safe to default/omit there (fixture shows `""`/`{}` when unset, not absent — worth
     confirming against a real not-yet-run request whether they're ever missing vs. always
     present-but-empty).
   - `LcoObservation`: `created: AstroPydanticTime`, `modified: AstroPydanticTime`,
     `ipp_value: float`, `name: str`, `observation_type: str`, `proposal: str`,
     `request_group_id: int`, `submitter: str`

2. **`get_object`/`create_object` injecting framework params as kwargs.**
   `Object.get_object` injects `comm`, `timezone`, `vfs`, `observer` into a config dict
   (`pyobs/object.py:467-480`), and `create_object` calls `klass(**cfg)` (`pyobs/object.py:187`).
   For a pydantic model those four land as constructor kwargs, which `extra="forbid"` then rejects.
   Failing tests: `tests/modules/robotic/test_scriptrunner.py` (2 tests), where
   `ScriptRunner.add_child_object(script, Script)` builds a `Script` from a dict.
   Fix: `create_object`/`get_object` must detect pydantic models and route framework params through
   pydantic's `context` (as `pyobs_model_validate` already does) instead of passing them as
   top-level kwargs.

3. **Top-level `class` key on non-polymorphic models.** `PolymorphicBaseModel` pops `class` in its
   deserialization validator, but plain `BaseModel` subclasses (e.g. `Task`) don't. Failing test:
   `tests/robotic/test_task.py::test_create_task`, whose fixture has `class: pyobs.robotic.Task`.
   Fix: either make `Task` a `PolymorphicBaseModel`, or pop `class` in the load path. Check which
   real task YAMLs carry a top-level `class` before deciding; the user's bug report did not.

## Latent bug this surfaced (separate from the above)

While tracing class 2 I found that a pydantic model built via `add_child_object`/`get_object`
currently gets `_comm = None`. `create_object` passes `comm` as a constructor kwarg, which pydantic
drops, and the `_inject_context_into_children` validator only reads `info.context`, which
`klass(**cfg)` never sets. Verified at runtime: `get_object({'class': '...Script'}, Script,
comm=<mock>)` yields `script._comm is None` and `script.comm` raises `AttributeError("No comm
available.")`. So `ScriptRunner._script` is a script that cannot reach comm today; nothing caught
it because the injected kwargs were being silently ignored. The class-2 fix (route framework params
through `context`) fixes this too, but it is worth flagging separately as a currently-broken
behavior that has been hidden by `extra="ignore"`.

## Resolved questions

- Class 3: make `Task` a `PolymorphicBaseModel`. It does receive `class` in real configs:
  `YamlTaskArchive` reads task YAMLs with `class: pyobs.robotic.Task` (see `test_task.py:38` and the
  docs examples), but `test_yaml_archives.py`'s `TASK_YAML` has no `class`. The polymorphic validator
  pops `class` when present and no-ops when absent, so it handles both. It also adds `class` to
  `Task.model_dump()`, which round-trips through `YamlObservationArchive` because `Observation.task`
  re-validates via `Task`'s polymorphic validator. `BackendTaskArchive` validates `Task` from backend
  JSON; whether that carries `class` is a sibling-repo question, but the polymorphic validator is
  harmless either way.
  - **Sibling-repo question closed** (checked against `pyobs-robotic-backend` source directly):
    `Observation.model_dump(use_task_id=True)` only embeds the full `Task` (now including `class`)
    when `task.id is None`; `BackendObservationArchive.add_observations`/`update_observation`
    (`pyobs/robotic/storage/backend/observationarchive.py:110,189`) are the only callers with
    `use_task_id=True`. In the actual runtime path, tasks always come from
    `BackendTaskArchive.get_schedulable_tasks()`, which loads them from `GET /api/tasks/` — always
    already carrying a server-assigned `id`. So `task.id is None` never occurs when
    `BackendObservationArchive` is paired with `BackendTaskArchive`. A hypothetical mixed config
    (e.g. `YamlTaskArchive`, whose tasks default to `id: None` unless the YAML sets one, paired with
    `BackendObservationArchive`) was already non-functional before this PR regardless of `class`:
    `pyobs-robotic-backend`'s `ObservationSerializer.task` is a plain Django `ForeignKey` with no
    custom field override, so DRF auto-generates a `PrimaryKeyRelatedField` that rejects a nested
    dict outright (`"Incorrect type. Expected pk value, received dict."`). And even where a task
    dict does legitimately reach the backend (`POST /api/tasks/`), `TaskSerializer.to_internal_value`
    already defensively strips a top-level `class` key (`if "class" in data: del data["class"]`).
    No behavior change in any reachable path.
- Class 2: `create_object` is only called from module-level `get_object` (`pyobs/object.py:101`),
  always with no args/kwargs. The four framework params are injected by `Object.get_object` into the
  config dict before `create_object` runs. Non-pydantic `Object` subclasses need them as real kwargs;
  pydantic models must get them via `model_validate(context=...)` instead. Branch on
  `issubclass(klass, pydantic.BaseModel)`.

## Implementation checklist

- [x] Set `extra="forbid"` on `pyobs.utils.serialization.BaseModel` (confirmed `PolymorphicBaseModel`
      inherits it).
- [x] Declare the missing fields on `LcoSchedulableRequest`, `LcoConfiguration`, and
      `LcoObservation` in `pyobs/robotic/storage/lco/_portal.py` (see field list above) — no
      `extra="ignore"` carve-out; the portal is self-hosted, so schema drift should fail loudly.
      Also surfaced (and fixed) a previously-hidden 4th breakage: `Merit.create()`
      (`pyobs/robotic/scheduler/merits/merit.py:40`) sets `config["class"]` from `config["type"]`
      but never removed `type`, so `extra="forbid"` rejected it once the LCO fixture-setup error
      that had been masking this stopped firing. Fixed by deleting `type` after deriving `class`.
      Also updated `tests/robotic/storage/lco/test_lcotask.py::test_from_observation`'s hand-rolled
      `obs_json` fixture, which predated the new required `LcoObservation` fields.
- [x] Fix `create_object`/`get_object` to inject `comm`/`timezone`/`vfs`/`observer` via pydantic
      `context` for pydantic models, not as constructor kwargs (branch on `issubclass(klass,
      pydantic.BaseModel)`). Implemented in `create_object` (`pyobs/object.py:164`): for pydantic
      `klass`, merges `kwargs` into `cfg`, pops the four framework params into a `context` dict, and
      calls `klass.model_validate(cfg, context=context)` instead of `klass(**cfg, **kwargs)`.
- [x] Make `Task` a `PolymorphicBaseModel` (class 3).
- [x] Set `extra="forbid"` on the imaging config models (`AcquisitionConfig`, `GuidingConfig`,
      `InstrumentConfig`, `Configuration` in `pyobs/robotic/scripts/imaging/imaging.py`) or switch
      them to `pyobs.utils.serialization.BaseModel`. Went with `ConfigDict(extra="forbid")` directly
      on each of the four rather than switching base classes — avoids pulling in
      `PrivateAttrMixin`/context-injection machinery none of them need.
- [x] Run the full test suite; confirm only the enumerated tests were fixed, no new failures.
      1462 passed, 25 skipped, 0 failed (`.venv/bin/pytest -m "not integration and not xmpp"`);
      `ruff check` clean on all changed files (`pyrefly check` clean in the main checkout; hit an
      unrelated environment quirk resolving `pyobs` inside the git worktree used for this PR,
      not a finding about the code).

## PR review follow-up (github.com/pyobs/pyobs-core/pull/762, thusser)

- **Fixed:** `Constraint.create()` (`pyobs/robotic/scheduler/constraints/constraint.py:47`) had the
  exact same stale-`type` bug as `Merit.create` — derived `class` from `type` but never removed
  `type`. `Constraint` is a `PolymorphicBaseModel`, so `extra="forbid"` now rejects it. No test
  caught it because every existing test passes `Constraint` instances, not `type`-shorthand dicts
  (the path `OnDemandScheduler(constraints=[{"type": "Airmass", ...}])` uses,
  `ondemandscheduler.py:59`). Fixed the same way as `Merit.create`, added
  `tests/robotic/scheduler/constraints/test_constraint.py` and
  `tests/robotic/scheduler/merits/test_merit.py` covering the `type`-shorthand path for both.
- **Fixed (minor):** `create_object`'s pydantic branch now passes `by_alias=True` to
  `model_validate` (matching `Merit.create`/`Constraint.create`'s existing convention) and asserts
  against positional `*args`, which `model_validate` can't accept.
- **Fixed (minor):** removed `Merit.create`'s dead "dotted `type`" branch — it never set `class` in
  the first place, so it was already broken before this PR; conditionally deleting `type` only
  inside that branch would have left it half-fixed.
- **Fixed — the required-fields concern was real, and worse than "might be missing sometimes":**
  checked against the actual portal source (`/home/husser/astro/monet/observation-portal`, LCO's
  Django app, our self-hosted deployment). `LcoSchedulableRequest`'s `state`/`submitter` are fine as
  required — `requestgroup_as_dict()` (`requestgroups/models.py:29-36`) always sets them
  unconditionally, and `RequestGroup.name`/`observation_type`/`operator`/`ipp_value`/`state` are all
  non-nullable Django model fields, confirmed by reading the model definition
  (`requestgroups/models.py:115-190`).

  `LcoObservation`'s 8 new fields (`created`, `modified`, `ipp_value`, `name`, `observation_type`,
  `proposal`, `request_group_id`, `submitter`) were wrong as required: **`Portal.observations()` and
  `Portal.download_schedule()` hit two different endpoints with two different response shapes**, and
  only one of them sends these fields.
  - `download_schedule()` calls `GET /api/observations/`, routed through `ListAsDictMixin.list()`
    (`common/mixins.py:8-13`), which calls `model.as_dict()` with no arguments →
    `Observation.as_dict(no_request=False)` (default) → `observation_as_dict()`
    (`observations/models.py:17-31`) sets all 8 fields unconditionally in the `no_request=False`
    branch. This is the shape `tests/robotic/storage/lco/conftest.py`'s `OBSERVATIONS_RESPONSE`
    fixture models, which is why the fields looked required from the fixtures alone.
  - `observations()` (called from `ObservationArchive.observations`,
    `observationarchive.py:179`) calls `GET /api/requests/{id}/observations/`, a custom action
    (`requestgroups/viewsets.py:311-315`) that explicitly calls `o.as_dict(no_request=True)` — the
    `no_request=True` branch in `observation_as_dict()` skips all 8 fields entirely, and `request`
    stays a plain FK id instead of being expanded into a nested object. Confirmed pyobs's own
    consumer (`observationarchive.py:179-193`) never reads those 8 fields anyway (only
    `id`/`start`/`end`/`state`) — they were dead weight for that path even before extra="forbid".

  Fixed by making all 8 fields `X | None = None` on `LcoObservation`. `request: int | LcoRequest`
  was already correct — it already tolerates both the bare-FK-id shape (`no_request=True`) and the
  expanded-object shape (`no_request=False`).
- Rebased onto `origin/develop`'s actual tip (previously the PR's recorded base was two commits
  stale, making the diff look like 14 files/3 commits instead of the true 12 files/2 commits).
- [x] Add a regression test: a task YAML with a misplaced key (the `guiding_config` inside
      `instrument_configs` case) raises `ValidationError` at load. Requires the imaging-models fix.
      Added `tests/robotic/scripts/test_imaging.py::test_misplaced_guiding_config_inside_instrument_configs_raises`.
- [x] Update this doc's `Status:` to `implemented` once landed.
