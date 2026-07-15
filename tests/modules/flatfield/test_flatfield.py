from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from pyobs.comm import Comm
from pyobs.interfaces import (
    BinningCapabilities,
    FiltersCapabilities,
    IBinning,
    ICamera,
    IFilters,
    IReady,
    ITelescope,
    ReadyState,
)
from pyobs.interfaces.IBinning import Binning
from pyobs.modules import Module
from pyobs.modules.flatfield.flatfield import FlatField
from pyobs.robotic.utils.skyflats import FlatFielder
from tests.helpers import make_proxy_cm


def _state_for(mock: AsyncMock, interface: object) -> object:
    """Find the state object set_state() was called with for the given interface."""
    for call in mock.await_args_list:
        if call.args[0] is interface:
            return call.args[1]
    raise AssertionError(f"set_state was never called with {interface}")


def make_flatfield(filters: str | None = None, flat_fielder: AsyncMock | None = None) -> FlatField:
    comm = MagicMock(spec=Comm)
    if flat_fielder is None:
        flat_fielder = AsyncMock(spec=FlatFielder)
        flat_fielder.has_filters = True
    return FlatField(telescope="telescope", camera="camera", flat_fielder=flat_fielder, filters=filters, comm=comm)


# ── __init__ ────────────────────────────────────────────────────────────────


def test_init_raises_when_filter_wheel_configured_without_filter_support() -> None:
    flat_fielder = AsyncMock(spec=FlatFielder)
    flat_fielder.has_filters = False

    with pytest.raises(ValueError):
        make_flatfield(filters="filter_wheel", flat_fielder=flat_fielder)


def test_init_accepts_filter_wheel_with_filter_support() -> None:
    flat_fielder = AsyncMock(spec=FlatFielder)
    flat_fielder.has_filters = True

    ff = make_flatfield(filters="filter_wheel", flat_fielder=flat_fielder)
    assert ff._filter_wheel == "filter_wheel"


# ── open ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_open_publishes_binning_and_ready_state(mocker) -> None:
    ff = make_flatfield()
    ff._comm.has_proxy = AsyncMock(return_value=True)
    ff._comm.register_event = AsyncMock()
    ff._comm.set_state = AsyncMock()
    mocker.patch.object(Module, "open", AsyncMock())

    await ff.open()

    binning_state = _state_for(ff._comm.set_state, IBinning)
    assert (binning_state.x, binning_state.y) == (1, 1)
    ready_state = _state_for(ff._comm.set_state, IReady)
    assert ready_state.ready is True


@pytest.mark.asyncio
async def test_open_does_not_publish_filter_state_when_unset(mocker) -> None:
    ff = make_flatfield()
    ff._comm.has_proxy = AsyncMock(return_value=True)
    ff._comm.register_event = AsyncMock()
    ff._comm.set_state = AsyncMock()
    mocker.patch.object(Module, "open", AsyncMock())

    await ff.open()

    for call in ff._comm.set_state.await_args_list:
        assert call.args[0] is not IFilters


@pytest.mark.asyncio
async def test_open_publishes_filter_state_once_set(mocker) -> None:
    ff = make_flatfield()
    ff._comm.has_proxy = AsyncMock(return_value=True)
    ff._comm.register_event = AsyncMock()
    ff._comm.set_state = AsyncMock()
    mocker.patch.object(Module, "open", AsyncMock())

    await ff.set_filter("clear")
    await ff.open()

    filter_state = _state_for(ff._comm.set_state, IFilters)
    assert filter_state.filter == "clear"


# ── close ───────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_close_sets_abort(mocker) -> None:
    ff = make_flatfield()
    mocker.patch.object(Module, "close", AsyncMock())

    assert not ff._abort.is_set()
    await ff.close()
    assert ff._abort.is_set()


# ── callback ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_callback_writes_to_publisher_when_configured() -> None:
    ff = make_flatfield()
    ff._publisher = AsyncMock()

    await ff.callback("2024-01-01", -5.0, 1.0, 30000.0, "clear", (1, 1))

    ff._publisher.assert_awaited_once_with(
        datetime="2024-01-01", solalt=-5.0, exptime=1.0, counts=30000.0, filter="clear", binning=1
    )


@pytest.mark.asyncio
async def test_callback_noop_without_publisher() -> None:
    ff = make_flatfield()
    assert ff._publisher is None

    # should not raise despite no publisher configured
    await ff.callback("2024-01-01", -5.0, 1.0, 30000.0, "clear", (1, 1))


# ── binning ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_binnings_returns_from_capabilities() -> None:
    ff = make_flatfield()
    camera = MagicMock(spec=ICamera)
    capabilities = BinningCapabilities(binnings=[Binning(x=1, y=1), Binning(x=2, y=2)])
    camera.get_capabilities = MagicMock(return_value=capabilities)
    ff._comm.proxy = MagicMock(return_value=make_proxy_cm(camera))

    binnings = await ff.list_binnings()

    assert binnings == [(1, 1), (2, 2)]


@pytest.mark.asyncio
async def test_list_binnings_empty_when_no_capabilities() -> None:
    ff = make_flatfield()
    camera = MagicMock(spec=ICamera)
    camera.get_capabilities = MagicMock(return_value=None)
    ff._comm.proxy = MagicMock(return_value=make_proxy_cm(camera))

    assert await ff.list_binnings() == []


@pytest.mark.asyncio
async def test_set_binning_updates_state_and_publishes() -> None:
    ff = make_flatfield()
    ff._comm.set_state = AsyncMock()

    await ff.set_binning(2, 2)

    assert ff._binning == (2, 2)
    ff._comm.set_state.assert_awaited_once()
    interface, state = ff._comm.set_state.await_args[0]
    assert interface is IBinning
    assert (state.x, state.y) == (2, 2)


# ── filters ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_filters_returns_from_capabilities() -> None:
    ff = make_flatfield()
    wheel = MagicMock(spec=IFilters)
    wheel.get_capabilities = MagicMock(return_value=FiltersCapabilities(filters=["clear", "red"]))
    ff._comm.proxy = MagicMock(return_value=make_proxy_cm(wheel))

    assert await ff.list_filters() == ["clear", "red"]


@pytest.mark.asyncio
async def test_list_filters_empty_when_no_capabilities() -> None:
    ff = make_flatfield()
    wheel = MagicMock(spec=IFilters)
    wheel.get_capabilities = MagicMock(return_value=None)
    ff._comm.proxy = MagicMock(return_value=make_proxy_cm(wheel))

    assert await ff.list_filters() == []


@pytest.mark.asyncio
async def test_set_filter_updates_state_and_publishes() -> None:
    ff = make_flatfield()
    ff._comm.set_state = AsyncMock()

    await ff.set_filter("red")

    assert ff._filter == "red"
    ff._comm.set_state.assert_awaited_once()
    interface, state = ff._comm.set_state.await_args[0]
    assert interface is IFilters
    assert state.filter == "red"


# ── flat_field ──────────────────────────────────────────────────────────────


def _ready_telescope() -> MagicMock:
    telescope = MagicMock(spec=ITelescope)
    telescope.get_state = MagicMock(return_value=ReadyState(ready=True))
    telescope.stop_motion = AsyncMock()
    return telescope


@pytest.mark.asyncio
async def test_flat_field_raises_when_already_running() -> None:
    ff = make_flatfield()
    ff._comm.proxy = MagicMock(return_value=make_proxy_cm(_ready_telescope()))

    block = asyncio.Event()

    async def blocking_call(*args: object, **kwargs: object) -> FlatFielder.State:
        await block.wait()
        return FlatFielder.State.FINISHED

    ff._flat_fielder.side_effect = blocking_call
    ff._flat_fielder.image_count = 0
    ff._flat_fielder.total_exptime = 0.0

    task = asyncio.create_task(ff.flat_field())
    await asyncio.sleep(0.05)

    with pytest.raises(ValueError):
        await ff.flat_field()

    block.set()
    await task


@pytest.mark.asyncio
async def test_flat_field_returns_when_telescope_not_ready() -> None:
    ff = make_flatfield()
    telescope = MagicMock(spec=ITelescope)
    telescope.get_state = MagicMock(return_value=ReadyState(ready=False))
    ff._comm.proxy = MagicMock(return_value=make_proxy_cm(telescope))
    ff._flat_fielder.image_count = 3
    ff._flat_fielder.total_exptime = 12.0

    count, exptime = await ff.flat_field()

    assert (count, exptime) == (3, 12.0)
    ff._flat_fielder.reset.assert_awaited_once()
    ff._flat_fielder.assert_not_called()


@pytest.mark.asyncio
async def test_flat_field_returns_when_aborted_mid_run() -> None:
    ff = make_flatfield()
    ff._comm.proxy = MagicMock(return_value=make_proxy_cm(_ready_telescope()))
    ff._flat_fielder.image_count = 1
    ff._flat_fielder.total_exptime = 2.0

    call_count = 0

    async def call_side_effect(*args: object, **kwargs: object) -> FlatFielder.State:
        nonlocal call_count
        call_count += 1
        await ff.abort()
        return FlatFielder.State.TESTING

    ff._flat_fielder.side_effect = call_side_effect

    count, exptime = await ff.flat_field()

    assert (count, exptime) == (1, 2.0)
    assert call_count == 1


@pytest.mark.asyncio
async def test_flat_field_completes_and_stops_telescope() -> None:
    ff = make_flatfield()
    telescope = _ready_telescope()
    ff._comm.proxy = MagicMock(return_value=make_proxy_cm(telescope))
    ff._flat_fielder.return_value = FlatFielder.State.FINISHED
    ff._flat_fielder.image_count = 20
    ff._flat_fielder.total_exptime = 123.4

    count, exptime = await ff.flat_field(count=5)

    assert (count, exptime) == (20, 123.4)
    ff._flat_fielder.reset.assert_awaited_once()
    ff._flat_fielder.assert_awaited_once_with(
        "telescope", "camera", count=5, binning=(1, 1), filters=None, filter_name=None
    )
    telescope.stop_motion.assert_awaited_once()


# ── abort ───────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_abort_sets_event() -> None:
    ff = make_flatfield()
    assert not ff._abort.is_set()
    await ff.abort()
    assert ff._abort.is_set()


@pytest.mark.asyncio
async def test_abort_weather_calls_abort() -> None:
    ff = make_flatfield()
    result = await ff._abort_weather(event=MagicMock(), sender="weather")
    assert ff._abort.is_set()
    assert result is True
