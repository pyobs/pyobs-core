from typing import Tuple
import astropy.units as u
from astropy.coordinates import SkyCoord, EarthLocation, AltAz, ICRS


def offset_altaz_to_radec(altaz: SkyCoord, dalt: float, daz: float) -> Tuple[float, float]:
    # convert to ra/dec
    p0 = altaz.transform_to(ICRS())
    p1 = altaz.spherical_offsets_by(daz * u.degree, dalt * u.degree).icrs

    # astropy hot-fix
    p0 = SkyCoord(ra=p0.ra, dec=p0.dec, frame="icrs")
    p1 = SkyCoord(ra=p1.ra, dec=p1.dec, frame="icrs")

    # offset
    dra, ddec = p0.spherical_offsets_to(p1)
    return float(dra.degree), float(ddec.degree)


def offset_radec_to_altaz(radec: SkyCoord, ra: float, dec: float, location: EarthLocation) -> Tuple[float, float]:
    # convert to alt/az
    altaz = AltAz(
        location=location,
        obstime=radec.obstime,
    )
    p0 = radec.transform_to(altaz)
    p1 = radec.spherical_offsets_by(ra * u.degree, dec * u.degree).transform_to(altaz)
    daz, dalt = p0.spherical_offsets_to(p1)
    return float(dalt.degree), float(daz.degree)
