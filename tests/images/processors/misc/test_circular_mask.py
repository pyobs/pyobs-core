import numpy as np
import pytest

from pyobs.images import Image
from pyobs.images.processors.misc import CircularMask


@pytest.mark.asyncio
async def test_call():
    radius = 50
    circular_mask = CircularMask(radius=radius)
    data = np.random.randint(1, 10, (500, 500))  # np.ones(500, 500)
    image = Image(data)
    image.header["CRPIX1"] = 250
    image.header["CRPIX2"] = 250
    masked_image = await circular_mask(image)

    assert image.data[250, 250] == masked_image.data[250, 250] > 0
    assert masked_image.data[400, 400] == 0
