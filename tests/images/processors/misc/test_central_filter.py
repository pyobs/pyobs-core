import numpy as np
import pytest

from pyobs.images import Image
from pyobs.images.processors.misc import CentralFilter


@pytest.mark.asyncio
async def test_call():
    radius = 50
    central_filter = CentralFilter(radius=radius)
    data = np.random.randint(1, 10, (500, 500))  # np.ones(500, 500)
    image = Image(data)
    image.header["CRPIX1"] = 250
    image.header["CRPIX2"] = 250
    filtered_image = await central_filter(image)

    assert image.data[250, 250] == filtered_image.data[250, 250] > 0
    assert filtered_image.data[400, 400] == 0
