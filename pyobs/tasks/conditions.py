from astroplan import Observer
from astropy.coordinates import SkyCoord

from pyobs.utils.time import Time


class ConditionsCache:
    def __init__(self, observer: Observer, roof: str, *args, **kwargs):
        """Creates a new conditions cache,

        Args:
            observer: Observer to use.
            roof: Name of roof module.
        """

        # store
        self._observer = observer
        self._roof = roof

        # the cache
        self._cache = {}

    def clear(self):
        """Clear the cache."""
        self._cache = {}

    def altaz(self, time: Time, coords: SkyCoord):
        """Returns alt/az for given coordinates at given time.

        Args:
            time: Time to return Alt/Az for.
            coords: Coordinates.

        Returns:
            Coordinates in Alt/Az.
        """

        # not in cache?
        if ('alt', coords, time) not in self._cache:
            # calculate
            self._cache[('alt', coords, time)] = self._observer.altaz(time, coords)

        # return it
        return self._cache[('alt', coords, time)]


__all__ = ['ConditionsCache']
