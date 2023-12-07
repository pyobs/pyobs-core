import logging

import numpy as np
import pytest

import scipy.ndimage

from pyobs.images import Image
from pyobs.images.processors.misc import Smooth


def test_init():
    sigma = 2
    order = 1
    mode = "constant"
    cval = 1.0
    truncate = 0

    smoother = Smooth(sigma, order, mode, cval, truncate)

    assert smoother.sigma == sigma
    assert smoother.order == order
    assert smoother.mode == mode
    assert smoother.cval == cval
    assert smoother.truncate == truncate


def test_init_default():
    smoother = Smooth(0)

    assert smoother.order == 0
    assert smoother.mode == "reflect"
    assert smoother.cval == 0.0
    assert smoother.truncate == 4.0


@pytest.mark.asyncio
async def test_call_no_image_data(caplog):
    image = Image()
    smoother = Smooth(1.0)

    with caplog.at_level(logging.WARNING):
        await smoother(image)

    assert caplog.records[0].message == "No data found in image."


@pytest.mark.asyncio
async def test_call(mocker):
    mocker.patch("scipy.ndimage.gaussian_filter", return_value=1)

    data = np.zeros((1, 1))
    image = Image(data=data)
    smoother = Smooth(1.0, 0, "reflect", 0.0, 4.0)

    result_image = await smoother(image)

    assert result_image.data == 1
    scipy.ndimage.gaussian_filter.assert_called_once_with(data, 1.0, order=0, mode="reflect", cval=0.0, truncate=4.0)
