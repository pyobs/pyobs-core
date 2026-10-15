"""Geometry metadata depends on position and site, not the mount's command interface."""

from unittest.mock import AsyncMock, MagicMock

import astropy.units as u
import pytest
from astroplan import Observer
from astropy.coordinates import SkyCoord
from astropy.utils import iers

from pyobs.comm import Comm
from pyobs.interfaces import AltAzState, IPointingAltAz, IPointingRaDec
from pyobs.modules.telescope.basetelescope import BaseTelescope
from pyobs.utils.time import Time


class PositionTelescope(BaseTelescope):
    position: tuple[float, float] | None = (20.0, 50.0)

    @property
    def _position_radec(self):
        return self.position

    async def _move_radec(self, ra, dec, abort_event):
        pass

    async def _move_altaz(self, alt, az, abort_event):
        pass

    async def _set_tracking_rate(self, ra_rate, dec_rate):
        pass

    async def init(self, **kwargs):
        pass

    async def park(self, **kwargs):
        pass

    async def stop_motion(self, **kwargs):
        pass


class RaDecOnlyTelescope(PositionTelescope, IPointingRaDec):
    pass


class AltAzTelescope(RaDecOnlyTelescope, IPointingAltAz):
    pass


GEOMETRY_CARDS = {"TEL-ALT", "TEL-AZ", "TEL-ZD", "AIRMASS", "MOONDIST", "SUNDIST"}
EQUATORIAL_CARDS = {"TEL-RA", "TEL-DEC", "RA", "DEC"}
CELESTIAL_CARDS = {"MOONALT", "MOONFRAC", "SUNALT"}


@pytest.fixture
def geometry_site(mocker):
    now = Time("2026-10-13T20:00:00")
    mocker.patch("pyobs.modules.telescope.basetelescope.Time.now", return_value=now)
    observer = Observer(latitude=52 * u.deg, longitude=10 * u.deg, elevation=100 * u.m)
    with iers.conf.set_temp("auto_download", False):
        yield observer, now


@pytest.mark.asyncio
@pytest.mark.parametrize("cls", [PositionTelescope, RaDecOnlyTelescope, AltAzTelescope])
@pytest.mark.parametrize("with_comm", [False, True])
async def test_geometry_values_and_interface_publication(geometry_site, cls, with_comm):
    observer, now = geometry_site
    comm = MagicMock(spec=Comm) if with_comm else None
    if comm is not None:
        comm.set_state = AsyncMock()
    tel = cls(observer=observer, comm=comm)
    assert isinstance(tel, IPointingAltAz) == (cls is AltAzTelescope)

    await tel._update_celestial_headers()
    header = await tel.get_fits_header_before()

    coords = SkyCoord(ra=20 * u.deg, dec=50 * u.deg, frame="icrs")
    altaz = observer.altaz(now, coords)
    assert altaz.alt.degree > 0
    expected = {
        "TEL-ALT": (float(altaz.alt.degree), "Telescope altitude [degrees]"),
        "TEL-AZ": (float(altaz.az.degree), "Telescope azimuth [degrees]"),
        "TEL-ZD": (90 - float(altaz.alt.degree), "Telescope zenith distance [degrees]"),
        "AIRMASS": (float(altaz.secz.value), "Airmass of observation start"),
        "MOONDIST": (float(altaz.separation(observer.moon_altaz(now)).degree), "Lunar distance from target"),
        "SUNDIST": (float(altaz.separation(observer.sun_altaz(now)).degree), "Solar Distance from Target"),
    }
    for key, (value, comment) in expected.items():
        assert header[key].value == pytest.approx(value)
        assert header[key].comment == comment
    assert {"LATITUDE", "LONGITUD", "HEIGHT"} <= header.keys()
    if isinstance(tel, IPointingRaDec):
        assert EQUATORIAL_CARDS <= header.keys()
        assert header["TEL-RA"].value == 20.0
        assert header["TEL-DEC"].value == 50.0
    else:
        assert EQUATORIAL_CARDS.isdisjoint(header)
    if comm is not None:
        if isinstance(tel, IPointingAltAz):
            comm.set_state.assert_awaited_once()
            interface, state = comm.set_state.await_args.args
            assert interface is IPointingAltAz
            assert isinstance(state, AltAzState)
            assert state.alt == pytest.approx(float(altaz.alt.degree))
            assert state.az == pytest.approx(float(altaz.az.degree))
        else:
            comm.set_state.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("cls", [RaDecOnlyTelescope, AltAzTelescope])
async def test_unknown_position_clears_separations(geometry_site, cls):
    observer, _ = geometry_site
    comm = MagicMock(spec=Comm)
    comm.set_state = AsyncMock()
    tel = cls(observer=observer, comm=comm)
    await tel._update_celestial_headers()
    assert {"MOONDIST", "SUNDIST"} <= tel._celestial_headers.keys()
    comm.set_state.reset_mock()

    tel.position = None
    await tel._update_celestial_headers()
    header = await tel.get_fits_header_before()
    assert GEOMETRY_CARDS.isdisjoint(header)
    assert EQUATORIAL_CARDS.isdisjoint(header)
    assert CELESTIAL_CARDS <= header.keys()
    comm.set_state.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("cls", [RaDecOnlyTelescope, AltAzTelescope])
async def test_no_observer_preserves_equatorial_headers(geometry_site, cls):
    comm = MagicMock(spec=Comm)
    comm.set_state = AsyncMock()
    tel = cls(observer=None, location=None, comm=comm)
    assert tel._observer is None
    await tel._update_celestial_headers()
    header = await tel.get_fits_header_before()
    assert EQUATORIAL_CARDS <= header.keys()
    assert (GEOMETRY_CARDS | CELESTIAL_CARDS).isdisjoint(header)
    comm.set_state.assert_not_awaited()


@pytest.mark.asyncio
async def test_geometry_namespace_filtering_and_static_precedence(geometry_site):
    observer, _ = geometry_site
    tel = RaDecOnlyTelescope(
        observer=observer,
        fits_namespaces={"camera": ["TEL-ALT"], "science": ["MOONDIST", "AIRMASS"]},
        fits_headers={"AIRMASS": [42.0, "Static override"]},
    )
    await tel._update_celestial_headers()
    header = await tel.get_fits_header_before(sender="camera", namespaces=["science"])
    assert set(header) == {"TEL-ALT", "MOONDIST", "AIRMASS"}
    assert header["AIRMASS"].value == 42.0
    assert set(await tel.get_fits_header_before(sender="camera")) == {"TEL-ALT"}
    assert await tel.get_fits_header_before(sender="unknown") == {}
