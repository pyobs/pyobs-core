import pytest
from astropy.coordinates import SkyCoord

from pyobs.images import Image
from pyobs.images.meta import SkyOffsets
from pyobs.images.processors.offsets import DummySkyOffsets


@pytest.mark.asyncio
async def test_call():
    coord0 = SkyCoord(alt=90.0, az=0.0, unit="degree", frame="altaz")
    coord1 = SkyCoord(alt=80.0, az=0.0, unit="degree", frame="altaz")

    offsets = DummySkyOffsets(coord0, coord1)
    image = Image()

    result_image = await offsets(image)

    result_offset = result_image.get_meta(SkyOffsets)

    assert result_offset.coord0.alt.deg == 90.0
    assert result_offset.coord0.az.deg == 0.0

    assert result_offset.coord1.alt.deg == 80.0
    assert result_offset.coord1.az.deg == 0.0
