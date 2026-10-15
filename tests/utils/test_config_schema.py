from __future__ import annotations

import dataclasses
import datetime
from enum import Enum, IntEnum
from typing import Annotated, Literal

import pytest
from pydantic import BaseModel, Field

from pyobs.utils.config_schema import (
    ConfigChoice,
    ConfigFieldSchema,
    ConfigSchema,
    dataclass_to_schema,
    pydantic_to_schema,
)
from pyobs.utils.enums import AccessLevel, Unit


class Mode(Enum):
    TRACK = "track"
    PARK = "park"


@dataclasses.dataclass
class PointingModel:
    az_offset: Annotated[float, Unit.ARCSEC] = 0.0


@dataclasses.dataclass
class SiderostatConfig:
    mode: Mode = Mode.TRACK
    exposure: float = 1.0
    pointing: PointingModel = dataclasses.field(default_factory=PointingModel)


def test_dataclass_to_schema_round_trips_nested_dataclass() -> None:
    schema = dataclass_to_schema(SiderostatConfig)

    assert schema == ConfigSchema(
        fields={
            "mode": ConfigFieldSchema(
                type="enum",
                options=["track", "park"],
                default="track",
                choices=[ConfigChoice("track", "track"), ConfigChoice("park", "park")],
            ),
            "exposure": ConfigFieldSchema(type="float", default=1.0),
            "pointing": ConfigFieldSchema(
                type="object",
                nested={"az_offset": ConfigFieldSchema(type="float", unit=Unit.ARCSEC, default=0.0)},
            ),
        }
    )


def test_dataclass_to_schema_unsupported_type_raises() -> None:
    @dataclasses.dataclass
    class BadConfig:
        ts: datetime.datetime

    with pytest.raises(TypeError):
        dataclass_to_schema(BadConfig)


def test_dataclass_to_schema_caches_per_class() -> None:
    assert dataclass_to_schema(SiderostatConfig) is dataclass_to_schema(SiderostatConfig)


def test_dataclass_to_schema_reads_level_from_metadata() -> None:
    @dataclasses.dataclass
    class Tiered:
        basic_field: float = dataclasses.field(default=1.0, metadata={"level": AccessLevel.BASIC})
        expert_field: float = dataclasses.field(default=2.0, metadata={"level": AccessLevel.EXPERT})
        hidden_field: int = dataclasses.field(default=0, metadata={"level": AccessLevel.HIDDEN})
        unset_field: int = 0

    schema = dataclass_to_schema(Tiered)

    assert schema.fields["basic_field"].level == AccessLevel.BASIC
    assert schema.fields["expert_field"].level == AccessLevel.EXPERT
    assert schema.fields["hidden_field"].level == AccessLevel.HIDDEN
    assert schema.fields["unset_field"].level == AccessLevel.BASIC


class InnerModel(BaseModel):
    channel: Literal[1, 3] = 1


class OuterModel(BaseModel):
    name: str
    mode: Literal["track", "park"] = "track"
    label: str | None = None
    extra: dict | None = None
    inner: InnerModel = InnerModel()


def test_pydantic_to_schema_round_trips_nested_model() -> None:
    schema = pydantic_to_schema(OuterModel)

    assert schema == ConfigSchema(
        fields={
            "name": ConfigFieldSchema(type="str", default=None),
            "mode": ConfigFieldSchema(
                type="enum",
                options=["track", "park"],
                default="track",
                choices=[ConfigChoice("track", "track"), ConfigChoice("park", "park")],
            ),
            "label": ConfigFieldSchema(type="str", default=None),
            "extra": ConfigFieldSchema(type="object", default=None),
            "inner": ConfigFieldSchema(
                type="object",
                nested={
                    "channel": ConfigFieldSchema(
                        type="enum", options=["1", "3"], default=1, choices=[ConfigChoice(1, "1"), ConfigChoice(3, "3")]
                    )
                },
            ),
        }
    )


def test_pydantic_to_schema_unsupported_type_raises() -> None:
    class BadModel(BaseModel):
        ts: datetime.datetime

    with pytest.raises(TypeError):
        pydantic_to_schema(BadModel)


def test_pydantic_to_schema_caches_per_class() -> None:
    assert pydantic_to_schema(OuterModel) is pydantic_to_schema(OuterModel)


def test_pydantic_to_schema_rejects_non_model() -> None:
    with pytest.raises(TypeError):
        pydantic_to_schema(dict)  # type: ignore[arg-type]


def test_pydantic_to_schema_reads_level_from_json_schema_extra() -> None:
    class Tiered(BaseModel):
        basic_field: float = Field(default=1.0, json_schema_extra={"level": AccessLevel.BASIC})
        expert_field: float = Field(default=2.0, json_schema_extra={"level": AccessLevel.EXPERT})
        hidden_field: int = Field(default=0, json_schema_extra={"level": AccessLevel.HIDDEN})
        unset_field: int = 0

    schema = pydantic_to_schema(Tiered)

    assert schema.fields["basic_field"].level == AccessLevel.BASIC
    assert schema.fields["expert_field"].level == AccessLevel.EXPERT
    assert schema.fields["hidden_field"].level == AccessLevel.HIDDEN
    assert schema.fields["unset_field"].level == AccessLevel.BASIC


def test_dataclass_to_schema_reads_description_from_metadata() -> None:
    @dataclasses.dataclass
    class Described:
        exposure: float = dataclasses.field(default=1.0, metadata={"description": "Exposure time"})
        unset_field: int = 0

    schema = dataclass_to_schema(Described)

    assert schema.fields["exposure"].description == "Exposure time"
    assert schema.fields["unset_field"].description is None


def test_pydantic_to_schema_prefers_json_schema_extra_description() -> None:
    """FTSConfigMain's convention: description lives in json_schema_extra, not Field(description=...)."""

    class Described(BaseModel):
        exposure: float = Field(default=1.0, json_schema_extra={"description": "Exposure time"})

    schema = pydantic_to_schema(Described)

    assert schema.fields["exposure"].description == "Exposure time"


def test_pydantic_to_schema_falls_back_to_native_field_description() -> None:
    class Described(BaseModel):
        exposure: float = Field(default=1.0, description="Exposure time")
        unset_field: int = 0

    schema = pydantic_to_schema(Described)

    assert schema.fields["exposure"].description == "Exposure time"
    assert schema.fields["unset_field"].description is None


def test_pydantic_to_schema_accepts_foreign_level_intenum() -> None:
    """A consumer without a pyobs-core dependency (e.g. pyftscontrol) defines its own local
    AccessLevel IntEnum with matching member values, per
    specs/steering/gui-field-access-levels.md, instead of importing this one. The schema must
    still recognize it by value.
    """

    class LocalAccessLevel(IntEnum):
        BASIC = 0
        EXPERT = 1
        HIDDEN = 2

    class Tiered(BaseModel):
        expert_field: float = Field(default=2.0, json_schema_extra={"level": LocalAccessLevel.EXPERT})

    schema = pydantic_to_schema(Tiered)

    assert schema.fields["expert_field"].level == AccessLevel.EXPERT


@pytest.mark.parametrize("value", [16416, 1.5, True, False, "001"])
def test_choice_types_and_labels_survive_nested_xml(value) -> None:
    # Construct a model dynamically so each literal retains its exact scalar type.
    from pydantic import create_model

    from pyobs.comm.xmpp.serializer import value_to_xml, xml_to_value

    model = create_model(
        "ChoiceModel",
        detector=(
            Literal[value],
            Field(default=value, json_schema_extra={"x-pyobs-choices": [{"value": value, "label": "Detector α"}]}),
        ),
    )
    wrapper = create_model("Wrapper", main=(model, ...))
    schema = pydantic_to_schema(wrapper)
    decoded = xml_to_value(value_to_xml(schema, ConfigSchema), ConfigSchema)
    field = decoded.fields["main"].nested["detector"]
    assert field.choices == [ConfigChoice(value, "Detector α")]
    assert type(field.choices[0].value) is type(value)
    assert type(field.default) is type(value)
    assert field.options == [str(value)]


def test_choice_labels_match_types_and_keep_full_domain() -> None:
    class Model(BaseModel):
        choice: Literal[1, 2, 3, "1", "001"] = Field(
            default=1,
            json_schema_extra={
                "x-pyobs-choices": [
                    {"value": True, "label": "wrong boolean"},
                    {"value": 1, "label": "Number"},
                    {"value": "1", "label": "Text"},
                    {"value": 2, "label": "conflict A"},
                    {"value": 2, "label": "conflict B"},
                    {"value": 999, "label": "outside domain"},
                    {"value": 3, "label": None},
                    None,
                ]
            },
        )

    field = pydantic_to_schema(Model).fields["choice"]
    assert field.choices == [
        ConfigChoice(1, "Number"),
        ConfigChoice(2, "2"),
        ConfigChoice(3, "3"),
        ConfigChoice("1", "Text"),
        ConfigChoice("001", "001"),
    ]


def test_numeric_dataclass_enum_metadata() -> None:
    class Detector(IntEnum):
        FIRST = 1
        SECOND = 2

    # Avoid postponed local annotations, which get_type_hints cannot resolve.
    model = dataclasses.make_dataclass(
        "Config",
        [
            (
                "detector",
                Detector,
                dataclasses.field(
                    default=Detector.FIRST, metadata={"x-pyobs-choices": [{"value": 1, "label": "First"}]}
                ),
            )
        ],
    )
    field = dataclass_to_schema(model).fields["detector"]
    assert field.options == ["1", "2"]
    assert field.choices == [ConfigChoice(1, "First"), ConfigChoice(2, "2")]
    assert type(field.default) is int


def test_choice_schema_old_and_new_xml_payloads() -> None:
    from pyobs.comm.xmpp.serializer import value_to_xml, xml_to_value

    @dataclasses.dataclass
    class LegacyField:
        type: str
        options: list[str] | None = None

    old = LegacyField(type="enum", options=["001", "1"])
    decoded = xml_to_value(value_to_xml(old, LegacyField), ConfigFieldSchema)
    assert decoded.choices is None
    assert decoded.options == old.options
    new = ConfigFieldSchema(type="enum", options=["1"], choices=[ConfigChoice(1, "Number")])
    legacy = xml_to_value(value_to_xml(new, ConfigFieldSchema), LegacyField)
    assert legacy == LegacyField(type="enum", options=["1"])


@pytest.mark.parametrize("value", [float("nan"), float("inf")])
def test_nonfinite_choice_rejected(value) -> None:
    from pydantic import create_model

    model = create_model("BadChoice", choice=(Literal[value], ...))
    with pytest.raises(TypeError, match="Unsupported configuration choice"):
        pydantic_to_schema(model)
