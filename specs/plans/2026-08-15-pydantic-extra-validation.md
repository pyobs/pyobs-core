# Plan: Make the pydantic config layer reject unknown keys (`extra="forbid"`)

Status: draft (investigation done, decision made, implementation not started)

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

1. **LCO portal payloads.** `pyobs/robotic/storage/lco/_portal.py` declares pydantic models that
   parse responses from the live LCO portal API. The API returns keys the models don't declare
   (e.g. `LcoSchedulableRequest` receives `submitter` and `state`). This is an external, not
   fully-controlled schema. Failing tests: `tests/robotic/storage/lco/test_lco_http.py`,
   `test_task.py`, `test_portal.py`, `test_schedulereader.py`, `test_schedulewriter.py`,
   `test_lcotask.py`.
   Fix: opt the LCO portal model family out with `model_config = ConfigDict(extra="ignore")` on
   `LcoSchedulableRequest` and the other portal models (or declare the missing fields). Keeping
   them tolerant is correct: forward-compatibility with an external API we don't version.

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
- Class 2: `create_object` is only called from module-level `get_object` (`pyobs/object.py:101`),
  always with no args/kwargs. The four framework params are injected by `Object.get_object` into the
  config dict before `create_object` runs. Non-pydantic `Object` subclasses need them as real kwargs;
  pydantic models must get them via `model_validate(context=...)` instead. Branch on
  `issubclass(klass, pydantic.BaseModel)`.

## Implementation checklist

- [ ] Set `extra="forbid"` on `pyobs.utils.serialization.BaseModel` (confirmed `PolymorphicBaseModel`
      inherits it).
- [ ] Add `extra="ignore"` (or declare the fields) on the LCO portal models in
      `pyobs/robotic/storage/lco/_portal.py`.
- [ ] Fix `create_object`/`get_object` to inject `comm`/`timezone`/`vfs`/`observer` via pydantic
      `context` for pydantic models, not as constructor kwargs (branch on `issubclass(klass,
      pydantic.BaseModel)`).
- [ ] Make `Task` a `PolymorphicBaseModel` (class 3).
- [ ] Set `extra="forbid"` on the imaging config models (`AcquisitionConfig`, `GuidingConfig`,
      `InstrumentConfig`, `Configuration` in `pyobs/robotic/scripts/imaging/imaging.py`) or switch
      them to `pyobs.utils.serialization.BaseModel`.
- [ ] Run the full test suite; confirm only the enumerated tests were fixed, no new failures.
- [ ] Add a regression test: a task YAML with a misplaced key (the `guiding_config` inside
      `instrument_configs` case) raises `ValidationError` at load. Requires the imaging-models fix.
- [ ] Update this doc's `Status:` to `implemented` once landed.
