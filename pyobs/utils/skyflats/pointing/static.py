import logging
from astropy.coordinates import SkyCoord
import astropy.units as u

from pyobs.interfaces import ITelescope
from pyobs.utils.threads import Future
from pyobs.utils.time import Time
from .base import SkyFlatsBasePointing


log = logging.getLogger(__name__)


class SkyFlatsStaticPointing(SkyFlatsBasePointing):
    """Static flat pointing."""
    __module__ = 'pyobs.utils.skyflats.pointing'

    def __init__(self, initialized: bool = False, *args, **kwargs):
        """Inits new static pointing for sky flats.

        Args:
            initialized: If False, telescope does not move at all.
        """

        SkyFlatsBasePointing.__init__(self, *args, **kwargs)

        # whether we've moved already
        self._initialized = initialized

    def __call__(self, telescope: ITelescope) -> Future:
        """Move telescope.

        Args:
            telescope: Telescope to use.

        Returns:
            Future for the movement call.
        """

        if self._initialized:
            return Future(empty=True)
        self._initialized = True

        # calculate Alt/Az position of sun
        sun = self.observer.sun_altaz(Time.now())
        log.info('Sun is currently located at alt=%.2f°, az=%.2f°', sun.alt.degree, sun.az.degree)

        # get sweet spot for flat-fielding
        altaz = SkyCoord(alt=80 * u.deg, az=sun.az + 180 * u.degree, obstime=Time.now(),
                         location=self.observer.location, frame='altaz')
        log.info('Sweet spot for flat fielding is at alt=80°, az=%.2f°', altaz.az.degree)

        # move telescope
        log.info('Moving telescope to Alt=80, Az=%.2f...', altaz.az.degree)
        return telescope.move_altaz(80, float(altaz.az.degree))

    def reset(self):
        """Reset pointing."""
        self._initialized = False


__all__ = ['SkyFlatsStaticPointing']
