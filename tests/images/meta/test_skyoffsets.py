import astropy
import pytest

from pyobs.images.meta import SkyOffsets
from astropy.coordinates import SkyCoord, BaseCoordinateFrame


def test_init():
    coord0 = SkyCoord(ra=0.0, dec=0.0, unit="deg")
    coord1 = SkyCoord(ra=1.0, dec=1.0, unit="deg")

    meta = SkyOffsets(coord0, coord1)

    assert meta.coord0.ra.deg == coord0.ra.deg
    assert meta.coord0.dec.deg == coord0.dec.deg

    assert meta.coord1.ra.deg == coord1.ra.deg
    assert meta.coord1.dec.deg == coord1.dec.deg


def test_to_frame_non_value():
    coord0 = SkyCoord(ra=0.0, dec=0.0, unit="deg")
    coord1 = SkyCoord(ra=1.0, dec=1.0, unit="deg")

    meta = SkyOffsets(coord0, coord1)

    framed_coord0, framed_coord1 = meta._to_frame()

    assert framed_coord0.ra.deg == coord0.ra.deg
    assert framed_coord0.dec.deg == coord0.dec.deg

    assert framed_coord1.ra.deg == coord1.ra.deg
    assert framed_coord1.dec.deg == coord1.dec.deg


def test_to_frame_w_value(mocker):
    """
    Tests that SkyCoord.transform_to is correctly used
    """
    frame = BaseCoordinateFrame()

    coord0 = SkyCoord(ra=0.0, dec=0.0, unit="deg")
    coord1 = SkyCoord(ra=1.0, dec=1.0, unit="deg")
    meta = SkyOffsets(coord0, coord1)

    mocker.patch("astropy.coordinates.SkyCoord.transform_to", return_value=0)

    x, y = meta._to_frame(frame)

    astropy.coordinates.SkyCoord.transform_to.assert_called_with(frame)

    assert x == 0
    assert y == 0


def test_separation(mocker):
    """
    Tests that _to_frame and separation is correctly used
    """
    # TODO: the commented out code probably needs to come back
    coord0 = SkyCoord(ra=0.0, dec=0.0, unit="deg")
    coord1 = SkyCoord(ra=1.0, dec=1.0, unit="deg")
    meta = SkyOffsets(coord0, coord1)

    mocker.patch.object(meta, "_to_frame", return_value=(coord0, coord1))
    #mocker.patch("astropy.coordinates.SkyCoord.separation", return_value=0)
    assert 1.41417766 == pytest.approx(meta.separation().degree)

    meta._to_frame.assert_called_once_with(None)
    #astropy.coordinates.SkyCoord.separation.assert_called_once_with(coord1)


def test_spherical_offsets(mocker):
    """
    Tests that _to_frame and spherical_offsets_to is correctly used
    """
    coord0 = SkyCoord(ra=0.0, dec=0.0, unit="deg")
    coord1 = SkyCoord(ra=1.0, dec=1.0, unit="deg")
    meta = SkyOffsets(coord0, coord1)

    mocker.patch.object(meta, "_to_frame", return_value=(coord0, coord1))
    mocker.patch("astropy.coordinates.SkyCoord.spherical_offsets_to", return_value=(0, 1))

    assert meta.spherical_offsets() == (0, 1)

    meta._to_frame.assert_called_once_with(None)
    astropy.coordinates.SkyCoord.spherical_offsets_to.assert_called_once_with(coord1.frame)
