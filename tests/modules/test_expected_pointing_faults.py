"""Exercise the actual pointing/flat-field handler registrations through execute()."""

import asyncio
from unittest.mock import AsyncMock

import astropy.units as u
import pytest
from astroplan import Observer
from astropy.utils import iers

from pyobs.comm.xmpp.rpc import reconstruct_fault
from pyobs.interfaces import IAbortable
from pyobs.modules.flatfield.flatfield import FlatField
from pyobs.modules.pointing._base import BasePointing
from pyobs.modules.telescope import DummyRaDecTelescope
from pyobs.modules.telescope.basetelescope import AltitudeLimitError
from pyobs.robotic.utils.skyflats import FlatFielder
from pyobs.utils import exceptions as exc
from pyobs.utils.enums import ModuleState, MotionStatus
from pyobs.utils.offsets import ApplyOffsets
from pyobs.utils.time import Time


class _FaultCaller:
    fault: exc.PyobsError

    async def abort(self, **kwargs):
        raise self.fault


class _PointingCaller(_FaultCaller, BasePointing, IAbortable):
    pass


class _FlatFieldCaller(_FaultCaller, FlatField, IAbortable):
    pass


def make_caller(kind):
    if kind == "pointing":
        caller = _PointingCaller(camera="camera", telescope="telescope", pipeline=[], apply=ApplyOffsets())
    else:
        fielder = AsyncMock(spec=FlatFielder)
        fielder.has_filters = True
        caller = _FlatFieldCaller(camera="camera", telescope="telescope", filters="filters", flat_fielder=fielder)
    caller._state = ModuleState.READY
    return caller


def remote_fault(cls, remote, message="rejected"):
    return reconstruct_fault(
        f"{cls.__module__}.{cls.__qualname__}",
        message,
        [f"{base.__module__}.{base.__qualname__}" for base in cls.__mro__[1:] if issubclass(base, exc.PyobsError)],
        remote,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "kind, remote",
    [
        ("pointing", "camera"),
        ("pointing", "telescope"),
        ("flatfield", "camera"),
        ("flatfield", "telescope"),
        ("flatfield", "filters"),
    ],
)
@pytest.mark.parametrize("expected", [True, False])
async def test_constructor_handlers_distinguish_expected_rejections_from_failures(kind, remote, expected):
    caller = make_caller(kind)
    failure_type = exc.MoveError if remote in {"telescope", "filters"} else exc.GrabImageError
    fault_type = AltitudeLimitError if expected else failure_type
    caller.fault = remote_fault(fault_type, remote)

    for attempt in range(3):
        with pytest.raises(fault_type) as raised:
            await caller.execute("abort", sender="test")
        assert raised.value.remote_module == remote
        await asyncio.sleep(0)
        if expected or attempt < 2:
            assert caller._state is ModuleState.READY
            assert caller._error_string == ""
        else:
            assert caller._state is ModuleState.ERROR
            assert "Severe error" in caller._error_string
    if expected:
        assert (exc.RemoteError, remote) not in caller._remote_exception_log


@pytest.mark.asyncio
async def test_real_dummy_altitude_rejections_do_not_disable_pointing(mocker):
    now = Time("2026-10-15T12:00:00")
    mocker.patch("pyobs.modules.telescope.basetelescope.Time.now", return_value=now)
    observer = Observer(latitude=52 * u.deg, longitude=10 * u.deg, elevation=100 * u.m)
    telescope = DummyRaDecTelescope(observer=observer)
    mocker.patch.object(telescope, "motion_status", return_value=MotionStatus.TRACKING)
    hardware_move = mocker.patch.object(telescope, "_move_radec", new_callable=AsyncMock)
    caller = make_caller("pointing")

    with iers.conf.set_temp("auto_download", False):
        for _ in range(3):
            with pytest.raises(AltitudeLimitError) as raised:
                await telescope.move_radec(0, -80)
            assert not isinstance(raised.value, exc.MotionError)
            caller.fault = remote_fault(type(raised.value), "telescope", raised.value.message)
            with pytest.raises(AltitudeLimitError):
                await caller.execute("abort", sender="test")
            await asyncio.sleep(0)
            assert caller._state is ModuleState.READY
            assert caller._error_string == ""
    hardware_move.assert_not_awaited()
    assert (exc.RemoteError, "telescope") not in caller._remote_exception_log
