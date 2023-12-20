from unittest.mock import Mock

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

    assert remover._background_remover._sigma_clip.sigma == sigma
    assert remover._background_remover._box_size == box_size
    assert remover._background_remover._filter_size == filter_size


def test_init_default():
    remover = RemoveBackground()
    assert remover._background_remover._sigma_clip.sigma == 3.0
    assert remover._background_remover._box_size == (50, 50)
    assert remover._background_remover._filter_size == (3, 3)


@pytest.mark.asyncio
async def test_call_const_background():
    sigma = 3.0
    box_size = (1, 1)
    filter_size = (3, 3)
    remover = RemoveBackground(sigma, box_size, filter_size)

    image = Image(data=np.ones((20, 20)))
    output_image = Image(data=np.ones((20, 20) * 2))
    remover._background_remover = Mock(return_value=output_image)

    result = await remover(image)

    np.testing.assert_array_equal(result.data, output_image.data)
    remover._background_remover.assert_called_once()
