from pyobs.images.meta import PixelOffsets


def test_pixeloffsets():
    dx = 1.0
    dy = 2.0

    meta = PixelOffsets(dx, dy)

    assert meta.dx == dx
    assert meta.dy == dy
