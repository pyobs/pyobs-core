import numpy as np
from astroplan import Observer
import astropy.units as u

from pyobs.modules.telescope import DummyTelescope
from pyobs.utils.time import Time


def test_calculate_derotator_position():
    telescope = DummyTelescope()
    telescope.observer = Observer(latitude=-32.375823 * u.deg, longitude=20.8108079 * u.deg, elevation=1798.0 * u.m)
    obstime = Time("2024-03-21T20:11:52.281735")
    ra = 138.01290730636728
    dec = -64.86351112618202
    tel_rot = -138.68173828124998
    alt = 57.24036032917521
    derot = telescope._calculate_derotator_position(ra, dec, alt, obstime)
    np.testing.assert_almost_equal(derot - tel_rot, 90.22, decimal=2)
