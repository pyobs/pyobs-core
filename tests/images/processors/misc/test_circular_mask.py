import numpy as np
import pytest

from pyobs.images import Image
from pyobs.images.processors.misc import CircularMask


@pytest.mark.asyncio
async def test_call():
    radius = 1
    circular_mask = CircularMask(radius=radius)
    data = np.ones((4, 4))
    image = Image(data)
    image.header["CRPIX1"] = 1.5
    image.header["CRPIX2"] = 1.5
    masked_image = await circular_mask(image)

    expected_output = np.array([[0, 0, 0, 0], [0, 1, 1, 0], [0, 1, 1, 0], [0, 0, 0, 0]])
    assert np.array_equal(masked_image.data, expected_output)
