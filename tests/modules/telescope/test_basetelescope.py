import math

import astropy.units as u
import numpy as np
import pytest
from astroplan import Observer

from pyobs.interfaces import OrbitalElements
from pyobs.modules.telescope import DummyRaDecTelescope
from pyobs.modules.telescope.basetelescope import (
    _orbital_plane_to_ecliptic_cartesian,
    _propagate_elements,
    _solve_barker_equation,
    _solve_kepler_equation,
)
from pyobs.utils.time import Time


def test_calculate_derotator_position():
    telescope = DummyRaDecTelescope(
        observer=Observer(latitude=-32.375823 * u.deg, longitude=20.8108079 * u.deg, elevation=1798.0 * u.m)
    )
    obstime = Time("2024-03-21T20:11:52.281735")
    ra = 138.01290730636728
    dec = -64.86351112618202
    tel_rot = -138.68173828124998
    alt = 57.24036032917521
    derot = telescope._calculate_derotator_position(ra, dec, alt, obstime)
    np.testing.assert_almost_equal(derot - tel_rot, 90.22, decimal=2)


# ── _solve_kepler_equation ───────────────────────────────────────────────────


def test_solve_kepler_equation_zero_mean_anomaly_gives_zero_eccentric_anomaly():
    assert _solve_kepler_equation(0.0, 0.3) == pytest.approx(0.0, abs=1e-12)


def test_solve_kepler_equation_pi_mean_anomaly_gives_pi_eccentric_anomaly():
    # symmetry point of Kepler's equation, holds for any eccentricity
    assert _solve_kepler_equation(math.pi, 0.7) == pytest.approx(math.pi, abs=1e-12)


@pytest.mark.parametrize("m,e", [(1.2, 0.6), (0.05, 0.95), (5.9, 0.2), (-2.3, 0.4)])
def test_solve_kepler_equation_residual_is_small(m, e):
    eccentric_anomaly = _solve_kepler_equation(m, e)
    m_wrapped = math.fmod(m, 2 * math.pi)
    residual = eccentric_anomaly - e * math.sin(eccentric_anomaly) - m_wrapped
    assert abs(residual) < 1e-10


def test_solve_kepler_equation_perihelion_and_aphelion_distance():
    a, e = 2.0, 0.4
    eccentric_anomaly = _solve_kepler_equation(0.0, e)
    r_perihelion = a * (1 - e * math.cos(eccentric_anomaly))
    assert r_perihelion == pytest.approx(a * (1 - e))

    eccentric_anomaly = _solve_kepler_equation(math.pi, e)
    r_aphelion = a * (1 - e * math.cos(eccentric_anomaly))
    assert r_aphelion == pytest.approx(a * (1 + e))


# ── _solve_barker_equation ───────────────────────────────────────────────────


def test_solve_barker_equation_zero_mean_anomaly_gives_zero():
    assert _solve_barker_equation(0.0) == pytest.approx(0.0, abs=1e-12)


@pytest.mark.parametrize("m", [0.7, -1.5, 3.0, 0.01])
def test_solve_barker_equation_residual_is_small(m):
    d = _solve_barker_equation(m)
    residual = d + d**3 / 3 - m
    assert abs(residual) < 1e-10


# ── _orbital_plane_to_ecliptic_cartesian ─────────────────────────────────────


def test_orbital_plane_rotation_identity_case():
    # w=0, Om=0, i=0: perifocal frame IS the ecliptic frame, so a point at true anomaly 0
    # (i.e. along +x in the perifocal plane) stays exactly on +x.
    x, y, z = _orbital_plane_to_ecliptic_cartesian(1.0, 0.0, 0.0, 0.0, 0.0)
    assert (x, y, z) == pytest.approx((1.0, 0.0, 0.0), abs=1e-12)


def test_orbital_plane_rotation_zero_inclination_stays_in_plane():
    # any orbit with inclination=0 must stay exactly in the ecliptic (z=0), regardless of
    # w/Om/true anomaly
    x, y, z = _orbital_plane_to_ecliptic_cartesian(0.6, -0.3, 123.0, 0.0, 45.0)
    assert z == pytest.approx(0.0, abs=1e-12)


def test_orbital_plane_rotation_argument_of_periapsis_rotates_within_plane():
    # w=90 rotates the periapsis direction itself by 90 deg within the (still flat) orbital plane
    x, y, z = _orbital_plane_to_ecliptic_cartesian(1.0, 0.0, 90.0, 0.0, 0.0)
    assert (x, y, z) == pytest.approx((0.0, 1.0, 0.0), abs=1e-12)


def test_orbital_plane_rotation_inclination_90_puts_pole_point_on_z_axis():
    # with i=90 and w=Om=0, the point 90 deg past the ascending node (true anomaly 90, since
    # periapsis coincides with the ascending node here) lands exactly on the ecliptic pole
    x, y, z = _orbital_plane_to_ecliptic_cartesian(0.0, 1.0, 0.0, 90.0, 0.0)
    assert (x, y, z) == pytest.approx((0.0, 0.0, 1.0), abs=1e-12)


# ── _propagate_elements ──────────────────────────────────────────────────────


def test_propagate_elements_requires_mean_anomaly_or_perihelion_time():
    elements = OrbitalElements(
        epoch=Time("2024-01-01T00:00:00"),
        semi_major_axis=2.0,
        eccentricity=0.1,
        inclination=5.0,
        longitude_ascending_node=10.0,
        argument_of_periapsis=20.0,
    )
    with pytest.raises(ValueError):
        _propagate_elements(elements, Time("2024-01-01T00:00:00"))


def test_propagate_elements_elliptical_returns_finite_radec():
    epoch = Time("2024-01-01T00:00:00")
    elements = OrbitalElements(
        epoch=epoch,
        semi_major_axis=2.2,
        eccentricity=0.15,
        inclination=7.0,
        longitude_ascending_node=80.0,
        argument_of_periapsis=30.0,
        mean_anomaly=10.0,
    )
    ra, dec = _propagate_elements(elements, epoch)
    assert 0.0 <= ra <= 360.0
    assert -90.0 <= dec <= 90.0


def test_propagate_elements_near_parabolic_returns_finite_radec():
    # Halley-like comet: a=17.8 AU, e=0.967 -> q ~ 0.587 AU
    epoch = Time("2024-01-01T00:00:00")
    elements = OrbitalElements(
        epoch=epoch,
        semi_major_axis=17.8,
        eccentricity=0.967,
        inclination=162.0,
        longitude_ascending_node=59.0,
        argument_of_periapsis=112.0,
        perihelion_time=epoch,
    )
    ra, dec = _propagate_elements(elements, epoch)
    assert 0.0 <= ra <= 360.0
    assert -90.0 <= dec <= 90.0

    # motion near perihelion for a q~0.6 AU comet should be on the order of a few deg/day --
    # not near-zero (elements wired up wrong) and not thousands of deg/day (q wildly off)
    ra2, dec2 = _propagate_elements(elements, epoch + 1 * u.day)
    moved_deg = math.hypot(ra2 - ra, dec2 - dec)
    assert 0.1 < moved_deg < 30.0
