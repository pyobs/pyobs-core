from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from pyobs.comm import Comm
from pyobs.interfaces import IStructuredConfig
from pyobs.modules import Module
from pyobs.modules.utils.dummystructuredconfig import (
    DummyNestedConfig,
    DummyOperatingMode,
    DummyStructuredConfig,
    DummyStructuredConfigData,
)


def _state_for(mock: AsyncMock, interface: object) -> object:
    """Find the most recent state object set_state() was called with for the given interface."""
    for call in reversed(mock.await_args_list):
        if call.args[0] is interface:
            return call.args[1]
    raise AssertionError(f"set_state was never called with {interface}")


def make_module(**kwargs) -> DummyStructuredConfig:
    comm = MagicMock(spec=Comm)
    return DummyStructuredConfig(comm=comm, **kwargs)


# ── __init__ ────────────────────────────────────────────────────────────────


def test_init_default_config() -> None:
    m = make_module()
    assert m._config == DummyStructuredConfigData()


# ── open ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_open_publishes_capabilities_and_state(mocker) -> None:
    m = make_module()
    m._comm.set_capabilities = AsyncMock()
    m._comm.set_state = AsyncMock()
    mocker.patch.object(Module, "open", AsyncMock())

    await m.open()

    m._comm.set_capabilities.assert_awaited_once()
    interface, schema = m._comm.set_capabilities.await_args[0]
    assert interface is IStructuredConfig
    assert schema.fields["name"].type == "str"
    assert schema.fields["count"].type == "int"
    assert schema.fields["offset"].type == "float"
    assert schema.fields["offset"].unit is not None
    assert schema.fields["verbose"].type == "bool"
    assert schema.fields["mode"].type == "enum"
    assert schema.fields["mode"].options == ["track", "park", "slew"]
    assert schema.fields["nested"].type == "object"
    assert schema.fields["nested"].nested is not None
    assert schema.fields["nested"].nested["threshold"].type == "int"

    state = _state_for(m._comm.set_state, IStructuredConfig)
    assert state.config == {
        "name": "dummy",
        "count": 1,
        "offset": 0.0,
        "verbose": False,
        "mode": "track",
        "nested": {"label": "nested", "threshold": 5, "active": True},
    }


# ── set_config ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_set_config_applies_and_publishes_state() -> None:
    m = make_module()
    m._comm.set_state = AsyncMock()

    await m.set_config(
        {
            "name": "renamed",
            "count": 7,
            "offset": 12.5,
            "verbose": True,
            "mode": "slew",
            "nested": {"label": "sub", "threshold": 42, "active": False},
        }
    )

    assert m._config == DummyStructuredConfigData(
        name="renamed",
        count=7,
        offset=12.5,
        verbose=True,
        mode=DummyOperatingMode.SLEW,
        nested=DummyNestedConfig(label="sub", threshold=42, active=False),
    )

    state = _state_for(m._comm.set_state, IStructuredConfig)
    assert state.config["name"] == "renamed"
    assert state.config["mode"] == "slew"
    assert state.config["nested"] == {"label": "sub", "threshold": 42, "active": False}


@pytest.mark.asyncio
async def test_set_config_partial_update_keeps_other_fields_at_default() -> None:
    m = make_module()
    m._comm.set_state = AsyncMock()

    await m.set_config({"count": 99})

    assert m._config.count == 99
    assert m._config.name == "dummy"


@pytest.mark.asyncio
async def test_set_config_int_accepts_float_with_whole_value() -> None:
    m = make_module()
    m._comm.set_state = AsyncMock()

    await m.set_config({"offset": 3})

    assert m._config.offset == 3.0
    assert isinstance(m._config.offset, float)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "bad_config",
    [
        {"bogus_field": 1},
        {"count": "not-an-int"},
        {"count": True},
        {"mode": "not-a-real-mode"},
        {"nested": "not-a-dict"},
        {"nested": {"threshold": "not-an-int"}},
    ],
)
async def test_set_config_raises_value_error_on_mismatch(bad_config) -> None:
    m = make_module()
    m._comm.set_state = AsyncMock()

    with pytest.raises(ValueError):
        await m.set_config(bad_config)

    # rejected config must not have been partially applied
    assert m._config == DummyStructuredConfigData()
    m._comm.set_state.assert_not_awaited()
