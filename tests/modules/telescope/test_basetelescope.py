import numpy as np
from pyobs.modules.telescope import DummyTelescope
from pyobs.utils.time import Time


def test_get_derotator_offset_from_header():
    telescope = DummyTelescope()
    obstime = Time("2024-03-21T20:11:52.281735")
    hdr = {
        "LATITUDE": (-32.375823, None),
        "LONGITUD": (20.810807999999998, None),
        "HEIGHT": (1798.0000000004793, None),
        "TEL-RA": (138.01290730636728, None),
        "TEL-DEC": (-64.86351112618202, None),
        "TEL-ROT": (-138.68173828124998, None),
        "TEL-ALT": (57.24036032917521, None),
    }
    np.testing.assert_almost_equal(telescope._get_derotator_offset_from_header(hdr, obstime), 90.22, decimal=2)
