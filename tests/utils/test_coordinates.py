from __future__ import annotations

import astropy.units as u
from astropy.coordinates import EarthLocation, SkyCoord
from astropy.time import Time

from pyobs.utils.coordinates import offset_altaz_to_radec, offset_radec_to_altaz

SAAO = EarthLocation.from_geodetic(lon=20.8108 * u.deg, lat=-32.3758 * u.deg, height=1798 * u.m)


def make_altaz(alt: float, az: float, time: str = "2025-11-03T23:00:00") -> SkyCoord:
    return SkyCoord(alt=alt * u.deg, az=az * u.deg, frame="altaz", location=SAAO, obstime=Time(time, scale="utc"))


def make_radec(ra: float, dec: float, time: str = "2025-11-03T23:00:00") -> SkyCoord:
    return SkyCoord(ra=ra * u.deg, dec=dec * u.deg, frame="icrs", obstime=Time(time, scale="utc"))


# ── offset_altaz_to_radec ─────────────────────────────────────────────────────


def test_offset_altaz_to_radec_zero_offset() -> None:
    """Zero offset returns (0, 0)."""
    altaz = make_altaz(45.0, 180.0)
    dra, ddec = offset_altaz_to_radec(altaz, 0.0, 0.0)
    assert abs(dra) < 1e-9
    assert abs(ddec) < 1e-9


def test_offset_altaz_to_radec_returns_floats() -> None:
    altaz = make_altaz(45.0, 90.0)
    dra, ddec = offset_altaz_to_radec(altaz, 0.1, 0.1)
    assert isinstance(dra, float)
    assert isinstance(ddec, float)


def test_offset_altaz_to_radec_small_offset() -> None:
    """Small offset produces small RA/Dec change."""
    altaz = make_altaz(60.0, 180.0)
    dra, ddec = offset_altaz_to_radec(altaz, 0.01, 0.01)
    assert abs(dra) < 0.1
    assert abs(ddec) < 0.1


def test_offset_altaz_to_radec_altitude_offset_affects_dec() -> None:
    """Pure altitude offset has stronger effect on dec than on RA near the meridian."""
    altaz = make_altaz(60.0, 180.0)  # due south = near meridian
    dra, ddec = offset_altaz_to_radec(altaz, 1.0, 0.0)
    assert abs(ddec) > abs(dra)


def test_offset_altaz_to_radec_sign_consistency() -> None:
    """Positive dalt should give positive ddec near meridian."""
    altaz = make_altaz(60.0, 180.0)
    dra_pos, ddec_pos = offset_altaz_to_radec(altaz, 1.0, 0.0)
    dra_neg, ddec_neg = offset_altaz_to_radec(altaz, -1.0, 0.0)
    assert ddec_pos > 0
    assert ddec_neg < 0


# ── offset_radec_to_altaz ─────────────────────────────────────────────────────


def test_offset_radec_to_altaz_zero_offset() -> None:
    """Zero RA/Dec offset returns (0, 0)."""
    radec = make_radec(83.82, 7.41)
    dalt, daz = offset_radec_to_altaz(radec, 0.0, 0.0, SAAO)
    assert abs(dalt) < 1e-9
    assert abs(daz) < 1e-9


def test_offset_radec_to_altaz_returns_floats() -> None:
    radec = make_radec(83.82, 7.41)
    dalt, daz = offset_radec_to_altaz(radec, 0.1, 0.1, SAAO)
    assert isinstance(dalt, float)
    assert isinstance(daz, float)


def test_offset_radec_to_altaz_small_offset() -> None:
    """Small RA/Dec offset produces small alt/az change."""
    radec = make_radec(83.82, 7.41)
    dalt, daz = offset_radec_to_altaz(radec, 0.01, 0.01, SAAO)
    assert abs(dalt) < 0.1
    assert abs(daz) < 0.1


def test_offset_radec_to_altaz_dec_changes_alt() -> None:
    """A pure Dec offset produces a non-zero altitude change."""
    radec = make_radec(75.0, -32.0)
    dalt, daz = offset_radec_to_altaz(radec, 0.0, 1.0, SAAO)
    assert abs(dalt) > 0.0


# ── round-trip consistency ────────────────────────────────────────────────────


def test_altaz_to_radec_round_trip() -> None:
    """Converting alt/az offset to RA/Dec and back gives approximately the original offset."""
    altaz = make_altaz(60.0, 180.0)
    dalt_in, daz_in = 0.1, 0.05

    dra, ddec = offset_altaz_to_radec(altaz, dalt_in, daz_in)

    # now convert back
    radec = altaz.icrs
    radec_coord = make_radec(float(radec.ra.deg), float(radec.dec.deg))
    dalt_out, daz_out = offset_radec_to_altaz(radec_coord, dra, ddec, SAAO)

    assert abs(dalt_out - dalt_in) < 0.01
    assert abs(daz_out - daz_in) < 0.01
