from typing import Any, Dict

import pytest
from astroplan import Observer
import astropy.units as u


class MockAcquisition:
    async def acquire_target(self, **kwargs: Any) -> Dict[str, Any]:
        return {"datetime": "", "ra": 0.0, "dec": 0.0, "az": 0.0, "alt": 0.0}


class MockTelescope:
    async def move_radec(*args: Any, **kwargs: Any) -> None:
        pass


@pytest.fixture(scope='module')
def observer():
    return Observer(longitude=20.8108 * u.deg, latitude=-32.375823 * u.deg,
                        elevation=1798.0 * u.m, timezone="UTC")