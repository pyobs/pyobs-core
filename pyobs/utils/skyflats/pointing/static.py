import logging
from typing import Any
from astropy.coordinates import SkyCoord
import astropy.units as u

from pyobs.interfaces import IPointingAltAz
from pyobs.utils.time import Time
from .base import SkyFlatsBasePointing

log = logging.getLogger(__name__)


class SkyFlatsStaticPointing(SkyFlatsBasePointing):
    """Static flat pointing."""

    __module__ = "pyobs.utils.skyflats.pointing"

    def __init__(self, initialized: bool = False, *args: Any, **kwargs: Any):
        """Inits new static pointing for sky flats.

        Args:
            initialized: If False, telescope does not move at all.
        """

        SkyFlatsBasePointing.__init__(self, *args, **kwargs)

        # whether we've moved already
        self._initialized = initialized

    async def __call__(self, telescope: IPointingAltAz) -> None:
        """Move telescope.

        Args:
            telescope: Telescope to use.

        Returns:
            Future for the movement call.
        """

        if self._initialized:
            return
        self._initialized = True

        # calculate Alt/Az position of sun
        now = Time.now()
        if self.observer is None:
            raise RuntimeError("Observer not initialized.")
        sun = self.observer.sun_altaz(now)
        log.info("Sun is currently located at alt=%.2f°, az=%.2f°", sun.alt.degree, sun.az.degree)

        # get sweet spot for flat-fielding
        altaz = SkyCoord(
            alt=80 * u.deg, az=sun.az + 180 * u.degree, obstime=now, location=self.observer.location, frame="altaz"
        )
        log.info("Sweet spot for flat fielding is at alt=80°, az=%.2f°", altaz.az.degree)

        # move telescope
        log.info("Moving telescope to Alt=80, Az=%.2f...", altaz.az.degree)
        return await telescope.move_altaz(80, float(altaz.az.degree))

    async def reset(self) -> None:
        """Reset pointing."""
        self._initialized = False


__all__ = ["SkyFlatsStaticPointing"]
