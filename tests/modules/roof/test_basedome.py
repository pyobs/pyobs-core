import asyncio
from typing import Any

import pytest

from pyobs.modules.roof import BaseDome
from pyobs.utils import exceptions as exc
from pyobs.utils.enums import ModuleState


class MockBaseDome(BaseDome):

    async def init(self, **kwargs: Any) -> None:
        pass

    async def park(self, **kwargs: Any) -> None:
        pass

    async def stop_motion(self, device: str | None = None, **kwargs: Any) -> None:
        pass

    async def move_altaz(self, alt: float, az: float, **kwargs: Any) -> None:
        pass

    async def get_altaz(self, **kwargs: Any) -> tuple[float, float]:
        return 60.0, 0.0


@pytest.mark.asyncio
async def test_get_fits_header_before(mocker):
    dome = MockBaseDome()

    from pyobs.interfaces import FitsHeaderEntry

    mocker.patch(
        "pyobs.modules.roof.BaseRoof.get_fits_header_before", return_value={"ROOF-OPN": FitsHeaderEntry(True, "")}
    )

    header = await dome.get_fits_header_before()

    assert "ROOF-OPN" in header
    assert header["ROOF-AZ"].value == 0.0
    assert header["ROOF-AZ"].comment == "Azimuth of roof slit, deg E of N"


def _make_failing_dome(error: exc.PyobsError) -> MockBaseDome:
    dome = MockBaseDome()

    async def _init(**kwargs: Any) -> None:
        raise error

    dome._methods["init"] = (_init, dome._methods["init"][1], dome._methods["init"][2])
    dome._state = ModuleState.READY
    return dome


@pytest.mark.asyncio
async def test_refused_init_does_not_escalate() -> None:
    """#1034: a refused init() (e.g. bad weather) must not put the dome module in ERROR."""
    dome = _make_failing_dome(exc.InitRefusedError("Weather seems to be bad."))
    for _ in range(4):
        with pytest.raises(exc.InitRefusedError):
            await dome.execute("init", sender="t")
        await asyncio.sleep(0.01)
    assert dome._state == ModuleState.READY


@pytest.mark.asyncio
async def test_failed_init_still_escalates() -> None:
    dome = _make_failing_dome(exc.InitError("PLC refused"))
    for _ in range(3):
        with pytest.raises(exc.InitError):
            await dome.execute("init", sender="t")
        await asyncio.sleep(0.01)
    assert dome._state == ModuleState.ERROR
