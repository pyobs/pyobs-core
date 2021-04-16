"""
Time (pyobs.utils.time)
-----------------------

TODO: write doc
"""

import datetime
import astropy.time
import astropy.units as u
import pytz
from astroplan import Observer


class Time(astropy.time.Time):
    """Hashable Time class."""
    _now_offset = astropy.time.TimeDelta(0 * u.second)

    def __hash__(self):
        if self.ndim != 0:
            raise TypeError("unhashable type: '{}'".format(self.__class__.__name__))
        return hash((self.jd1, self.jd2, self.scale))

    @classmethod
    def set_offset_to_now(cls, delta: astropy.time.TimeDelta):
        cls._now_offset = delta

    @classmethod
    def now(cls):
        """
        Creates a new object corresponding to the instant in time this
        method is called.

        .. note::
            "Now" is determined using the `~datetime.datetime.utcnow`
            function, so its accuracy and precision is determined by that
            function.  Generally that means it is set by the accuracy of
            your system clock.

        Returns:
            A new `Time` object (or a subclass of `Time` if this is called from
            such a subclass) at the current time.
        """
        # call `utcnow` immediately to be sure it's ASAP
        dtnow = datetime.datetime.utcnow()
        return cls(val=dtnow, format='datetime', scale='utc') + cls._now_offset

    def night_obs(self, observer: Observer) -> datetime.date:
        """Returns the night for this time, i.e. the date of the start of the current night.

        Args:
            observer: Observer object to use.

        Returns:
            Night for this time.
        """

        # convert to datetime
        time = self.datetime

        # get local datetime
        utc_dt = pytz.utc.localize(time)
        loc_dt = utc_dt.astimezone(observer.timezone)

        # get night
        if loc_dt.hour < 15:
            loc_dt += datetime.timedelta(days=-1)
        return loc_dt.date()


__all__ = ['Time']
