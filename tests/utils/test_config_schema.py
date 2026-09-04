from __future__ import annotations

import dataclasses
import datetime
from enum import Enum, IntEnum
from typing import Annotated, Literal

import pytest
from pydantic import BaseModel, Field

from pyobs.utils.config_schema import ConfigFieldSchema, ConfigSchema, dataclass_to_schema, pydantic_to_schema
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
            "mode": ConfigFieldSchema(type="enum", options=["track", "park"], default=Mode.TRACK),
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
            "mode": ConfigFieldSchema(type="enum", options=["track", "park"], default="track"),
            "label": ConfigFieldSchema(type="str", default=None),
            "extra": ConfigFieldSchema(type="object", default=None),
            "inner": ConfigFieldSchema(
                type="object",
                nested={"channel": ConfigFieldSchema(type="enum", options=["1", "3"], default=1)},
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
