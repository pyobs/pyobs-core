from typing import Any, Dict, List

import pytest
from astroplan import Observer, ObservingBlock, FixedTarget
import astropy.units as u
from astropy.coordinates import SkyCoord


class MockAcquisition:
    async def acquire_target(self, **kwargs: Any) -> Dict[str, Any]:
        return {"datetime": "", "ra": 0.0, "dec": 0.0, "az": 0.0, "alt": 0.0}


class MockTelescope:
    async def move_radec(*args: Any, **kwargs: Any) -> None:
        pass


@pytest.fixture(scope='module')
def observer() -> Observer:
    return Observer(longitude=20.8108 * u.deg, latitude=-32.375823 * u.deg,
                        elevation=1798.0 * u.m, timezone="UTC")


@pytest.fixture(scope='module')
def schedule_blocks() -> List[ObservingBlock]:
    blocks = [
        ObservingBlock(
            FixedTarget(SkyCoord(0.0 * u.deg, 0.0 * u.deg, frame="icrs"), name=str(i)), 10 * u.minute, 10,
            constraints=[], configuration={"request": {"id": str(i)}}
        )
        for i in range(10)
    ]

    return blocks
