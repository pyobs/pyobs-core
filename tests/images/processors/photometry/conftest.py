import numpy as np
import pytest
from astropy.io.fits import Header
from astropy.table import QTable

from pyobs.images import Image


@pytest.fixture(scope="module")
def const_test_image() -> Image:
    data = np.ones((100, 100))
    header = Header({"CD1_1": 1.0})
    catalog = QTable({"x": [40.0], "y": [40.0]})
    return Image(data=data, header=header, catalog=catalog)
