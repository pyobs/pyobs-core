from typing import Any, Tuple, Optional

import pytest

from pyobs.modules.roof import BaseDome


class TestBaseDome(BaseDome):

    async def init(self, **kwargs: Any) -> None:
        pass

    async def park(self, **kwargs: Any) -> None:
        pass

    async def stop_motion(self, device: Optional[str] = None, **kwargs: Any) -> None:
        pass

    async def move_altaz(self, alt: float, az: float, **kwargs: Any) -> None:
        pass

    async def get_altaz(self, **kwargs: Any) -> Tuple[float, float]:
        return 60.0, 0.0


@pytest.mark.asyncio
async def test_get_fits_header_before(mocker):
    dome = TestBaseDome()

    mocker.patch("pyobs.modules.roof.BaseRoof.get_fits_header_before", return_value={"ROOF-OPN": (True, "")})

    header = await dome.get_fits_header_before()

    assert "ROOF-OPN" in header
    assert header["ROOF-AZ"] == (0.0, "Azimuth of roof slit, deg E of N")
