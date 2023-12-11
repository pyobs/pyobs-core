import numpy as np
import photutils.background
import pytest

from pyobs.images import Image
from pyobs.images.processors.misc import RemoveBackground


def test_init():
    sigma = 1.0
    box_size = (10, 10)
    filter_size = (3, 3)
    remover = RemoveBackground(sigma, box_size, filter_size)

    assert remover.sigma == sigma
    assert remover.box_size == box_size
    assert remover.filter_size == filter_size


def test_init_default():
    remover = RemoveBackground()
    assert remover.sigma == 3.0
    assert remover.box_size == (50, 50)
    assert remover.filter_size == (3, 3)


@pytest.mark.asyncio
async def test_call_const_background(mocker):
    sigma = 3.0
    box_size = (1, 1)
    filter_size = (3, 3)
    spy = mocker.spy(photutils.background.Background2D, "__init__")
    remover = RemoveBackground(sigma, box_size, filter_size)

    image = Image(data=np.ones((20, 20)))
    output_image = await remover(image)

    spy.assert_called_once()
    np.testing.assert_array_equal(output_image.data, np.zeros((20, 20)))