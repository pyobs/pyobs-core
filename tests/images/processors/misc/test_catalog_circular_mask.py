import numpy as np
import pytest

from astropy.table import Table
from pyobs.images import Image
from pyobs.images.processors.misc import CatalogCircularMask


@pytest.mark.asyncio
async def test_call():
    radius = 1
    mask = CatalogCircularMask(radius=radius)
    data = np.ones((4, 4))
    catalog = Table([[1, 3], [1, 3]], names=("x", "y"))
    image = Image(data, catalog=catalog)
    image.header["CRPIX1"] = 1.5
    image.header["CRPIX2"] = 1.5
    image.header["XBINNING"] = 1
    image.header["YBINNING"] = 1
    masked_image = await mask(image)
    expected_output_catalog = Table([[1], [1]], names=("x", "y"))
    assert masked_image.catalog == expected_output_catalog
