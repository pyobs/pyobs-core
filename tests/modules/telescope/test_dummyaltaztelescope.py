from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import astropy.units as u
import pytest
from astroplan import Observer

from pyobs.comm import Comm
from pyobs.events import OffsetsAltAzEvent
from pyobs.interfaces import IOffsetsAltAz
from pyobs.modules.telescope.dummyaltaztelescope import DummyAltAzTelescope


def make_dummyaltaztelescope(**kwargs) -> DummyAltAzTelescope:
    comm = MagicMock(spec=Comm)
    comm.get_own_state = MagicMock(return_value=None)
    comm.get_own_capabilities = MagicMock(return_value=None)
    comm.set_state = AsyncMock()
    comm.set_capabilities = AsyncMock()
    comm.send_event = AsyncMock()
    comm.register_event = AsyncMock()

    observer = kwargs.pop("observer", None)
    if observer is None:
        observer = Observer(latitude=52.0 * u.deg, longitude=10.0 * u.deg, elevation=100.0 * u.m)
    kwargs.setdefault("min_altitude", -90)
    kwargs.setdefault("location", observer.location)
    return DummyAltAzTelescope(comm=comm, observer=observer, **kwargs)


@pytest.mark.asyncio
async def test_open_registers_offsets_altaz_event_and_publishes_initial_state():
    tel = make_dummyaltaztelescope(offsets=(1.5, -2.5))
    await tel.open()

    registered = {call.args[0] for call in tel._comm.register_event.await_args_list}
    assert OffsetsAltAzEvent in registered

    interface, state = tel._comm.set_state.await_args_list[-1].args
    assert interface is IOffsetsAltAz
    assert state.alt == pytest.approx(1.5)
    assert state.az == pytest.approx(-2.5)


@pytest.mark.asyncio
async def test_set_offsets_altaz_sends_event_and_updates_state():
    tel = make_dummyaltaztelescope(move_accuracy=0.0)
    await tel.open()

    await tel.set_offsets_altaz(3.0, -1.0)

    event = tel._comm.send_event.await_args.args[0]
    assert isinstance(event, OffsetsAltAzEvent)
    assert event.alt == pytest.approx(3.0)
    assert event.az == pytest.approx(-1.0)

    assert tel._altaz_offsets == pytest.approx((3.0, -1.0))

    interface, state = tel._comm.set_state.await_args.args
    assert interface is IOffsetsAltAz
    assert state.alt == pytest.approx(3.0)
    assert state.az == pytest.approx(-1.0)
