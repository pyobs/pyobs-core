# Plan: honor exclude/include/by_alias/exclude_* on PolymorphicBaseModel

Status: proposed

Tracks issue #855. Repos: pyobs-core only.

## Problem

`PolymorphicBaseModel.inject_class_on_serialization()` (`pyobs/utils/serialization.py:43-49`) is
a `@model_serializer(mode="wrap")` that never calls its `handler` and doesn't even accept an
`info: SerializationInfo` parameter — it hand-builds the output dict via raw `getattr()` over
`type(self).model_fields`. Every `model_dump()`/`model_dump_json()` call on `Task`, `Script`,
`Constraint`, `Merit`, `Target` (and their concrete leaf subclasses) silently ignores `exclude`,
`include`, `by_alias`, `exclude_none`, `exclude_unset`, and `exclude_defaults` instead of raising
— confirmed for `exclude` (`#855`'s own repro) and independently confirmed here for `by_alias`
(`Task.static_target` has `alias="target"`; `model_dump(by_alias=True)` still keys it
`static_target`).

The `handler`-bypass itself is deliberate (existing comment: avoids Pydantic v2 resolving field
schemas against the abstract base type when nested in a parent model) and stays as-is — this plan
only adds the missing `info`-driven filtering on top of the existing hand-rolled dict.

### What's confirmed still broken after a flat-field-only fix, and deliberately out of scope

Nested exclude/include specs (`{"constraints": {0: {"cost"}}}`, `"__all__"` keys, mixing `True`
with nested dicts in the same call) are **not** propagated into child `PolymorphicBaseModel`
values today, and this plan does not attempt to fix that — reimplementing pydantic's own
include/exclude grammar generically (index/`__all__` keys for sequences, recursive forwarding into
nested `.model_dump()` calls) is real, separate engineering effort that nothing in the fleet
currently needs (every existing caller — `Scheduler._content_dump()`,
`PortalTaskArchive._task_content_dump()` — only ever passes a flat set of top-level field names).
Instead of silently doing the wrong thing (today's behavior) or silently doing a *partial* thing,
an unsupported request must raise `NotImplementedError` — loud failure over silent wrong output,
consistent with how this codebase already treats bad input at other boundaries (see
`pyobs/utils/serialization.py`'s own `resolve_polymorphic_type_shorthand`, which raises
`ValueError` on an unmatched `type` rather than passing it through).

## Design

### 1. Signature change

```python
@model_serializer(mode="wrap")
def inject_class_on_serialization(
    self, handler: ValidatorFunctionWrapHandler, info: SerializationInfo
) -> dict[str, Any]:
```

Import `SerializationInfo` from `pydantic_core.core_schema` (already imports
`ValidatorFunctionWrapHandler` from there).

### 2. Reject what isn't supported, before building anything

Add a helper, e.g. `_flat_field_spec(spec: Any, info_kwarg: str) -> set[str] | None`, called once
each for `info.exclude` and `info.include`:

- `None` → `None` (no restriction).
- A `set`/`frozenset` of field names → returned as-is (already flat).
- A `dict` where every value is exactly `True` → returned as `set(spec.keys())` (pydantic's
  "exclude this whole field" shorthand, flat).
- Anything else (a dict with a non-`True` value anywhere, i.e. a nested spec; an int key, i.e. a
  sequence-index spec) → `raise NotImplementedError(
    f"PolymorphicBaseModel.model_dump() only supports flat field-name {info_kwarg}= "
    f"(no nested specs) — got {spec!r} for {type(self).__name__}; see pyobs-core#855"
  )`.

Also raise `NotImplementedError` up front if `info.exclude_computed_fields` is set and
`type(self)` declares any `@computed_field` — grep confirms **no** current
`PolymorphicBaseModel` subclass has one, so this branch is currently dead code, but it's a silent
trap waiting for the first computed field otherwise. Implement the check generically (e.g. via
`type(self).__pydantic_decorators__.computed_fields`) rather than skipping it because it's
unreachable today.

`round_trip`, `context`, and serialization `mode` (python vs. json) need no handling here — they
already flow through correctly today because nested field values (themselves `BaseModel`
instances) are serialized by pydantic-core's own runtime-type dispatch on the returned dict's
values, independent of anything this function does. Confirmed by testing: a nested
`Constraint` inside `Task.constraints` already comes back as a fully-serialized dict via its own
`model_serializer`, even though today's `getattr()` never calls `.model_dump()` on it explicitly.
This plan doesn't touch that mechanism.

### 3. Apply the flat filters when building the dict

```python
exclude = self._flat_field_spec(info.exclude, "exclude")
include = self._flat_field_spec(info.include, "include")
fields = type(self).model_fields
names = [
    n for n in fields
    if (include is None or n in include)
    and (exclude is None or n not in exclude)
]

result: dict[str, Any] = {}
for name in names:
    value = getattr(self, name)
    if info.exclude_none and value is None:
        continue
    if info.exclude_unset and name not in self.model_fields_set:
        continue
    if info.exclude_defaults and value == fields[name].get_default(call_default_factory=True):
        continue
    key = fields[name].alias if (info.by_alias and fields[name].alias) else name
    result[key] = value
result["class"] = f"{self.__module__}.{self.__class__.__name__}"
return result
```

`"class"` is always emitted regardless of any of the above — it isn't a declared field and
`retrieve_class_on_deserialization` needs it for every round-trip; this matches current behavior
and needs no new test (already covered by every existing polymorphic round-trip test).

Note `get_default(call_default_factory=True)` for `exclude_defaults` — several fields here use
`default_factory` (`constraints: list = Field(default_factory=list)` etc.), and comparing against
the *factory result* (not the raw `FieldInfo.default`, which is `PydanticUndefined` for
factory-defaulted fields) is what makes `exclude_defaults` behave the same as it would on a
plain (non-polymorphic) model.

### 4. Tests (`tests/utils/test_serialization.py` — new file, or nearest existing one if a
   `PolymorphicBaseModel`-focused test file already exists — check before creating)

Run each of these against **`Task`** (has an aliased field, `static_target`/`target`) and
**one other subclass with no alias**, e.g. `AirmassConstraint`, both standalone and nested under
an abstract-typed parent field (`Task.constraints: list[Constraint]`) to confirm the
abstract-type-resolution behavior the `handler`-bypass exists for still holds:

- `exclude={"field_name"}` (flat set) drops exactly that key.
- `exclude={"field_name": True}` (flat dict form) behaves identically to the set form.
- `include={"a", "b"}` keeps only those keys (plus `"class"`).
- `by_alias=True` on `Task` emits `"target"` not `"static_target"`; `by_alias=True` on a
  subclass with no aliased fields is a no-op (sanity check it doesn't error).
- `exclude_none=True` drops a field currently `None` (e.g. `Task.static_target` when unset).
- `exclude_defaults=True` drops a factory-defaulted field left untouched (e.g. `constraints=[]`)
  and keeps one explicitly set to a non-default value.
- `exclude_unset=True` drops a field never passed to the constructor.
- `exclude={"a": {"b"}}` (nested spec) raises `NotImplementedError` — both for `Task` directly and
  for a nested `Constraint` inside `Task.constraints` (i.e. `Task.model_dump(exclude={
  "constraints": {0: {"cost"}}})` must raise, not silently ignore, since the outer `Task` call
  is where pydantic would normally resolve and forward that spec).
- Regression: a plain `model_dump()` (no kwargs) is byte-for-byte unchanged from current behavior
  for both `Task` and the chosen subclass — guards against the filter logic accidentally
  reordering keys or dropping something when nothing was asked to be excluded.
- Regression: nested nesting still resolves subclass-specific fields correctly (the original
  reason for the `handler`-bypass) — e.g. `Task.model_dump()` with a `Constraint` subclass in
  `constraints` still includes that subclass's own fields, not just `Constraint`'s base fields.

### 5. Optional follow-up cleanup (not part of this plan; do only if separately asked)

Once this lands, `Scheduler._content_dump()` (`pyobs/modules/robotic/scheduler.py:269-282`,
introduced in `3b06cf16`, 2026-09-01, "fix: address review findings on #848 scheduler reschedule
fix" — the commit that filed #855) and `PortalTaskArchive._task_content_dump()`
(`pyobs/robotic/storage/portal/taskarchive.py`, added for #856) could both switch from
"dump-then-pop" to `model_dump(exclude={"updated_at"})` directly,
removing the pop-after-dump workaround and its docstrings explaining *why* it's there. Low value,
purely cosmetic, and touches code that's already correct — leave alone unless requested.

## Acceptance criteria

- [ ] `inject_class_on_serialization` accepts `info: SerializationInfo` and honors flat
      `exclude`/`include`/`by_alias`/`exclude_none`/`exclude_defaults`/`exclude_unset`.
- [ ] Any nested (non-flat) `exclude`/`include` spec raises `NotImplementedError` instead of being
      silently ignored or partially applied.
- [ ] Plain `model_dump()` (no kwargs) output is unchanged for every existing caller — no
      regression in current scheduler/task-archive/portal-import tests.
- [ ] New tests listed above pass.
- [ ] `ruff`/`pyrefly` clean; full non-integration suite green.

## Out of scope

- Nested/indexed exclude-include spec support (see "What's confirmed still broken" above) —
  raises `NotImplementedError` instead.
- Removing the `Scheduler._content_dump()` / `PortalTaskArchive._task_content_dump()` workarounds
  (§5 above) — optional, separate, not required for this issue to be considered fixed.
