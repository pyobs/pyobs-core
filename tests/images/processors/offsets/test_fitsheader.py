import pytest
from astropy.io.fits import Header

from pyobs.images import Image
from pyobs.images.meta.genericoffset import GenericOffset
from pyobs.images.processors.offsets import FitsHeaderOffsets


def test_attribute_validation() -> None:
    with pytest.raises(ValueError):
        FitsHeaderOffsets(("a", "b", "c"), ("a", "b", "c"))


@pytest.mark.asyncio
async def test_call() -> None:
    header = Header({"A1": 4, "A2": 2, "B1": 2, "B2": 1})
    image = Image(header=header)
    processor = FitsHeaderOffsets(("A1", "A2"), ("B1", "B2"))
    result = await processor(image)

    offset = result.get_meta(GenericOffset)
    assert offset.dx == 2
    assert offset.dy == 1


@pytest.mark.asyncio
async def test_call_default() -> None:
    header = Header({"A1": 4, "A2": 2, "DET-CPX1": 2, "DET-CPX2": 1})
    image = Image(header=header)
    processor = FitsHeaderOffsets(("A1", "A2"))
    result = await processor(image)

    offset = result.get_meta(GenericOffset)
    assert offset.dx == 2
    assert offset.dy == 1