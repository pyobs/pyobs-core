"""
TODO: write doc
"""

__title__ = "Time"

from datetime import UTC, date, datetime, time, timedelta
from typing import cast

import astropy.time
import astropy.units as u
from astroplan import Observer


class Time(astropy.time.Time):
    """Hashable Time class."""

    _now_offset = astropy.time.TimeDelta(0 * u.second)

    def __hash__(self) -> int:
        if self.ndim != 0:
            raise TypeError(f"unhashable type: '{self.__class__.__name__}'")
        return hash((self.jd1, self.jd2, self.scale))

    @classmethod
    def set_offset_to_now(cls, delta: astropy.time.TimeDelta) -> None:
        """Shifts what :meth:`now` returns by ``delta``, without affecting the system clock.

        For simulation/testing scenarios that need to run at an arbitrary point in time.
        """
        cls._now_offset = delta

    @classmethod
    def now(cls) -> "Time":
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
        dtnow = datetime.now(UTC)
        return cast(Time, Time(val=dtnow, format="datetime", scale="utc") + Time._now_offset)

    def night_obs(self, observer: Observer) -> date:
        """Returns the night for this time, i.e. the date of the start of the current night.

        The boundary is local civil noon in the observer's timezone. All times from
        noon until the next noon use the local date of the sunset after that opening
        noon, keeping evening exposures and morning calibrations on the same night.
        If no sunset is found (e.g. polar day/night), use the query's local calendar
        date instead; that fallback can change at midnight.

        Args:
            observer: Observer object to use.

        Returns:
            Night for this time.
        """

        timezone = observer.timezone
        local_time = self.to_datetime(timezone=timezone)
        noon_date = local_time.date()
        if local_time.hour < 12:
            noon_date -= timedelta(days=1)
        noon = datetime.combine(noon_date, time(12))
        # Localize the anchor independently: the query may have crossed a DST change
        # since that noon. pytz requires localize(), while other tzinfo uses replace().
        if hasattr(timezone, "localize"):
            noon = timezone.localize(noon)
        else:
            noon = noon.replace(tzinfo=timezone)
        sunset = observer.sun_set_time(Time(noon), which="next")
        if sunset.masked:
            # sun doesn't cross the horizon within the search window, e.g. polar day/night,
            # so fall back to the observer's local calendar date
            return cast(date, local_time.date())
        return sunset.to_datetime(timezone=timezone).date()


__all__ = ["Time"]
