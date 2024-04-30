import pytest
from astroplan import Observer
import astropy.units as u

@pytest.fixture(scope='module')
def observer():
    return Observer(longitude=20.8108 * u.deg, latitude=-32.375823 * u.deg,
                        elevation=1798.0 * u.m, timezone="UTC")