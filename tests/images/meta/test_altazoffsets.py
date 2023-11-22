from pyobs.images.meta import AltAzOffsets


def test_alt_az_offsets():
    dalt = 1.0
    daz = 2.0

    meta = AltAzOffsets(dalt, daz)

    assert meta.dalt == dalt
    assert meta.daz == daz
