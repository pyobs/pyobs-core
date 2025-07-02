from pyobs.images.meta import RaDecOffsets


def test_radecoffsets():
    dra = 1.0
    ddec = 2.0

    meta = RaDecOffsets(dra, ddec)

    assert meta.dra == dra
    assert meta.ddec == ddec
