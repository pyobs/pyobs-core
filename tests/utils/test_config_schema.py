from __future__ import annotations

import dataclasses
import datetime
from enum import Enum
from typing import Annotated, Literal

import pytest
from pydantic import BaseModel

from pyobs.utils.config_schema import ConfigFieldSchema, ConfigSchema, dataclass_to_schema, pydantic_to_schema
from pyobs.utils.enums import Unit


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
