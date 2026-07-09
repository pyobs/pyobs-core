import numpy as np
from astropy import constants
from astropy.coordinates import SkyCoord, get_sun

from pyobs.utils.time import Time

from .target import Target


class HeliocentricPolar(Target):
    mu: float
    psi: float

    @property
    def coord(self) -> SkyCoord:
        return self.coordinates(Time.now())

    def coordinates(self, time: Time) -> SkyCoord:
        from sunpy.coordinates import Helioprojective

        # to helioprojective
        alpha = np.arccos(self.mu)
        d_sun = get_sun(time).distance  # distance earth <-> sun
        r_sun = constants.R_sun  # type: ignore[missing-attribute] # radius of sun

        # get the angle between target and the line between earth and sun
        # from the triangle defined by the distance between earth and sun, the
        # distance between target and sun and the angle included by them
        theta = np.arctan(r_sun * np.sin(alpha) / (d_sun - (r_sun * self.mu)))

        # calculate helio projective cartesian coordinates
        tx = -theta * np.sin(self.psi)
        ty = theta * np.cos(self.psi)
        return SkyCoord(tx, ty, obstime=Time.now(), frame=Helioprojective, observer="earth")

    def __str__(self) -> str:
        return f"{self.name} ({self.coord})"


__all__ = ["HeliocentricPolar"]
