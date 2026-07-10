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
