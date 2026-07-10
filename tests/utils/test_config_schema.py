from __future__ import annotations

import dataclasses
import datetime
from enum import Enum
from typing import Annotated

import pytest

from pyobs.utils.config_schema import ConfigFieldSchema, ConfigSchema, dataclass_to_schema
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
