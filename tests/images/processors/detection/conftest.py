import pytest
from astropy.table import QTable

from pyobs.images import Image


@pytest.fixture()
def gaussian_sources_image() -> Image:
    from photutils.datasets import make_gaussian_prf_sources_image, make_noise_image

    shape = (100, 100)

    table = QTable()
    table["amplitude"] = [200, 70, 150, 210]
    table["x_0"] = [30, 25, 80, 90]
    table["y_0"] = [10, 40, 25, 60]
    table["sigma"] = [1, 2, 1.0, 1]

    data = make_gaussian_prf_sources_image(shape, table)
    noise = make_noise_image(shape, distribution="gaussian", mean=5.0, stddev=0)

    return Image(data + noise, catalog=table)
