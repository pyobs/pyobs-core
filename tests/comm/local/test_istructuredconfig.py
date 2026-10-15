"""Tests for IStructuredConfig capabilities/state round-tripping through LocalComm."""

from __future__ import annotations

import dataclasses
from typing import Any

import pytest

from pyobs.comm.local.localcomm import LocalComm
from pyobs.comm.local.localnetwork import LocalNetwork
from pyobs.interfaces import ConfigAppliedState, IStructuredConfig
from pyobs.utils.config_schema import dataclass_to_schema


@dataclasses.dataclass
class DummyConfig:
    exposure: float = 1.0


class DummyStructuredConfigModule(IStructuredConfig):
    def __init__(self, comm: LocalComm) -> None:
        self.comm = comm
        self._config = DummyConfig()

    async def set_config(self, config: dict[str, Any], **kwargs: Any) -> None:
        self._config = dataclasses.replace(self._config, **config)
        await self.comm.set_state(IStructuredConfig, ConfigAppliedState(config=dataclasses.asdict(self._config)))


@pytest.fixture(autouse=True)
def reset_network():
    """Reset LocalNetwork singleton before each test."""
    LocalNetwork._instance = None
    yield
    LocalNetwork._instance = None


@pytest.mark.asyncio
async def test_get_capabilities_returns_schema() -> None:
    """Comm.get_capabilities(module, IStructuredConfig) returns the published ConfigSchema."""
    camera = LocalComm("camera")
    observer = LocalComm("observer")

    schema = dataclass_to_schema(DummyConfig)
    await camera.set_capabilities(IStructuredConfig, schema)

    result = await observer.get_capabilities("camera", IStructuredConfig)
    assert result is not None
    assert result.fields["exposure"].type == "float"


@pytest.mark.asyncio
async def test_set_config_round_trips_via_published_state() -> None:
    """set_config on a module applies the config and publishes a matching ConfigAppliedState."""
    camera = LocalComm("camera")
    observer = LocalComm("observer")
    module = DummyStructuredConfigModule(camera)

    received: list[ConfigAppliedState] = []
    await observer.subscribe_state("camera", IStructuredConfig, received.append)

    await module.set_config({"exposure": 2.5})

    assert len(received) == 1
    assert received[0].config == {"exposure": 2.5}


@pytest.mark.asyncio
async def test_typed_choice_capability_and_config_state() -> None:
    from typing import Literal

    from pydantic import BaseModel, Field

    from pyobs.utils.config_schema import pydantic_to_schema

    class Config(BaseModel):
        detector: Literal[16416, 16417] = Field(
            default=16416,
            json_schema_extra={"x-pyobs-choices": [{"value": 16416, "label": "Detector A"}]},
        )

    camera = LocalComm("camera")
    observer = LocalComm("observer")
    await camera.set_capabilities(IStructuredConfig, pydantic_to_schema(Config))
    caps = await observer.get_capabilities("camera", IStructuredConfig)
    assert caps is not None
    assert caps.fields["detector"].choices is not None
    choice = caps.fields["detector"].choices[0]
    assert choice.label == "Detector A"
    assert type(choice.value) is int
    config = Config.model_validate({"detector": choice.value})
    received: list[ConfigAppliedState] = []
    await observer.subscribe_state("camera", IStructuredConfig, received.append)
    await camera.set_state(IStructuredConfig, ConfigAppliedState(config=config.model_dump()))
    assert type(received[0].config["detector"]) is int
