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

    expected_data = np.ones((4, 4))
    expected_mask = np.array(
        [
            [True, True, True, True],
            [True, False, False, True],
            [True, False, False, True],
            [True, True, True, True],
        ]
    )
    assert np.array_equal(masked_image.data, expected_data)
    assert np.array_equal(masked_image.mask, expected_mask)
