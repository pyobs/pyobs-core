import pytest

from pyobs.images import Image
from pyobs.images.meta import PixelOffsets
from pyobs.images.processors.offsets import DummyOffsets


@pytest.mark.asyncio
async def test_dummy_offsets() -> None:
    offsets = DummyOffsets("pyobs.images.meta.PixelOffsets", 10.0)
    image = Image()

    output_image = await offsets(image)
    offset = output_image.get_meta(PixelOffsets)
    assert offset.dx == 10.0
    assert offset.dy == 10.0
