import pytest
from pydantic_core import PydanticSerializationError

from pyobs.robotic.scheduler.constraints.airmassconstraint import AirmassConstraint
from pyobs.robotic.task import Task


def make_task(**kwargs: object) -> Task:
    return Task(id=1, name="t1", duration=100.0, **kwargs)  # type: ignore[arg-type]


# ── exclude/include: flat forms ─────────────────────────────────────────────────────────────


def test_exclude_flat_set_drops_field() -> None:
    d = make_task().model_dump(exclude={"updated_at"})
    assert "updated_at" not in d
    assert "id" in d


def test_exclude_flat_dict_true_matches_set_form() -> None:
    t = make_task()
    assert t.model_dump(exclude={"updated_at": True}) == t.model_dump(exclude={"updated_at"})


def test_include_keeps_only_named_fields_plus_class() -> None:
    d = make_task().model_dump(include={"id", "name"})
    assert set(d.keys()) == {"id", "name", "class"}


def test_exclude_flat_on_nested_subclass_field() -> None:
    c = AirmassConstraint(max_airmass=2.0)
    d = c.model_dump(exclude={"target_dependent"})
    assert "target_dependent" not in d
    assert d["max_airmass"] == 2.0
    assert d["class"].endswith("AirmassConstraint")


# ── by_alias ─────────────────────────────────────────────────────────────────────────────────


def test_by_alias_uses_task_target_alias() -> None:
    d = make_task().model_dump(by_alias=True)
    assert "target" in d
    assert "static_target" not in d


def test_by_alias_no_op_when_no_aliased_fields() -> None:
    c = AirmassConstraint(max_airmass=2.0)
    assert c.model_dump(by_alias=True) == c.model_dump()


# ── exclude_none / exclude_defaults / exclude_unset ─────────────────────────────────────────


def test_exclude_none_drops_unset_optional_field() -> None:
    d = make_task().model_dump(exclude_none=True)
    assert "static_target" not in d  # defaults to None, never set


def test_exclude_defaults_drops_factory_default_and_keeps_explicit_value() -> None:
    d = make_task().model_dump(exclude_defaults=True)
    assert "constraints" not in d  # untouched default_factory=list

    d2 = make_task(constraints=[AirmassConstraint(max_airmass=2.0)]).model_dump(exclude_defaults=True)
    assert "constraints" in d2


def test_exclude_unset_drops_field_never_passed_to_constructor() -> None:
    d = make_task().model_dump(exclude_unset=True)
    assert "priority" not in d  # never passed, even though it has a non-None default
    assert "id" in d  # explicitly passed in make_task()


# ── nested (unsupported) specs raise ────────────────────────────────────────────────────────
#
# The NotImplementedError raised inside inject_class_on_serialization never reaches the caller
# as-is: pydantic-core wraps any exception a model_serializer function raises into its own
# PydanticSerializationError, embedding the original type/message in the wrapped text. That's
# pydantic-core's behavior for every @model_serializer, not something this fix controls.


def test_nested_exclude_spec_raises_on_direct_call() -> None:
    with pytest.raises(PydanticSerializationError, match="NotImplementedError"):
        make_task().model_dump(exclude={"static_target": {"name"}})


def test_nested_exclude_spec_on_child_field_raises_from_parent_call() -> None:
    t = make_task(constraints=[AirmassConstraint(max_airmass=2.0)])
    with pytest.raises(PydanticSerializationError, match="NotImplementedError"):
        t.model_dump(exclude={"constraints": {0: {"cost"}}})


def test_nested_include_spec_raises() -> None:
    with pytest.raises(PydanticSerializationError, match="NotImplementedError"):
        make_task().model_dump(include={"static_target": {"name"}})


# ── regressions ──────────────────────────────────────────────────────────────────────────────


def test_plain_dump_unchanged_for_task() -> None:
    t = make_task()
    assert t.model_dump() == {
        "id": 1,
        "name": "t1",
        "project": "",
        "duration": 100.0,
        "priority": 1.0,
        "constraints": [],
        "merits": [],
        "static_target": None,
        "script": {},
        "active": True,
        "updated_at": None,
        "class": "pyobs.robotic.task.Task",
    }


def test_plain_dump_unchanged_for_subclass() -> None:
    c = AirmassConstraint(max_airmass=2.0)
    assert c.model_dump() == {
        "cost": 2.0,
        "target_dependent": True,
        "max_airmass": 2.0,
        "class": "pyobs.robotic.scheduler.constraints.airmassconstraint.AirmassConstraint",
    }


def test_nested_subclass_fields_still_resolved_under_abstract_parent_field() -> None:
    """Guards the reason inject_class_on_serialization bypasses `handler` in the first place:
    a Constraint subclass nested in Task.constraints (typed list[Constraint]) must still dump
    its own subclass-specific fields (max_airmass), not just Constraint's base fields."""
    t = make_task(constraints=[AirmassConstraint(max_airmass=2.0)])
    d = t.model_dump()
    assert d["constraints"] == [
        {
            "cost": 2.0,
            "target_dependent": True,
            "max_airmass": 2.0,
            "class": "pyobs.robotic.scheduler.constraints.airmassconstraint.AirmassConstraint",
        }
    ]
