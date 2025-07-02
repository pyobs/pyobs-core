import pytest
from astropy.table import QTable

from pyobs.images import Image


@pytest.fixture()
def gaussian_sources_image() -> Image:
    from photutils.datasets import make_model_image, make_noise_image
    from astropy.modeling import models

    shape = (100, 100)
    model = models.Moffat2D()

    table = QTable()
    table["amplitude"] = [200, 70, 150, 210]
    table["x_0"] = [30, 25, 80, 80]
    table["y_0"] = [20, 40, 25, 60]
    table["gamma"] = [1, 2, 1.0, 1]
    table["alpha"] = [1, 2, 1.0, 1]

    model_shape = (15, 15)
    data = make_model_image(shape, model, table, model_shape=model_shape)
    noise = make_noise_image(shape, distribution="gaussian", mean=5.0, stddev=0)

    return Image(data + noise, catalog=table)
