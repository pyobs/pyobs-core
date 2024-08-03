from datetime import datetime, timezone, timedelta, tzinfo, date
import functools
import logging
from typing import Union, Optional, Any, Dict
import pytz
from astropy.coordinates import EarthLocation, Longitude, SkyCoord, ICRS, get_sun, AltAz
from pyobs.utils.time import Time


log = logging.getLogger(__name__)


class Environment:
    """An Environment object hold information about the location of the observatory and provides some convenience
    methode.

    An object of this type is usually never instantiated manually, but is part of a :class:`~pyobs.modules.Module`,
    automatically created from the configuration file like this::

        timezone: Africa/Johannesburg
        location:
            longitude: 20.810808
            latitude: -32.375823
            elevation: 1798.
    """

    def __init__(
        self, timezone: str = "utc", location: Union[Dict[str, Any], EarthLocation] = None, *args: Any, **kwargs: Any
    ):
        # get timezone
        self._timezone = pytz.timezone(timezone)
        log.info("Using timezone %s.", timezone)

        # get location
        self._location: Optional[EarthLocation] = None
        if location is not None:
            if isinstance(location, EarthLocation):
                # store directly
                self._location = location
            elif isinstance(location, dict):
                # dictionary?
                if (
                    "longitude" in location
                    and location["longitude"] is not None
                    and "latitude" in location
                    and location["latitude"] is not None
                    and "elevation" in location
                    and location["elevation"] is not None
                ):
                    self._location = EarthLocation(location["longitude"], location["latitude"], location["elevation"])
                else:
                    log.error("Location must be provided as dict of longitude/latitude/elevation values.")
            else:
                # nothing
                log.error("Could not initialize location.")
        if self._location is not None:
            log.info(
                "Setting location to longitude=%s, latitude=%s, and elevation=%s.",
                self._location.lon,
                self._location.lat,
                self._location.height,
            )

    @property
    def timezone(self) -> tzinfo:
        """Returns the timezone of the observatory."""
        return self._timezone

    @property
    def location(self) -> Optional[EarthLocation]:
        """Returns the location of the observatory."""
        return self._location

    @functools.lru_cache()
    def localtime(self, utc: Optional[datetime] = None) -> datetime:
        """Returns the local time at the observatory, either for a given UTC time or for now, if none is given.

        Args:
            utc: UTC to convert. Use now if none is given.

        Returns:
            Local time.
        """
        # get UTC
        if utc is None:
            utc = datetime.now(timezone.utc)
        # mark as UTC
        utc_dt = pytz.utc.localize(utc)
        # convert to local timezone
        return utc_dt.astimezone(self._timezone)

    @functools.lru_cache()
    def night_obs(self, time: Optional[Union[datetime, Time]] = None) -> date:
        """Returns the date of the night for the given night, i.e. the date of the start of the night.

        Args:
            time: Time to return night for. If none is given, current time is used.

        Returns:
            Night of observation.
        """

        # None given?
        if time is None:
            time = Time.now()

        # convert to Time
        if isinstance(time, Time):
            time = time.datetime

        # get local datetime
        if not isinstance(time, datetime):
            raise ValueError("Invalid time")
        utc_dt = pytz.utc.localize(time)
        loc_dt = utc_dt.astimezone(self._timezone)

        # get night
        if loc_dt.hour < 15:
            loc_dt += timedelta(days=-1)
        return loc_dt.date()

    @functools.lru_cache()
    def lst(self, time: Union[datetime, Time]) -> Longitude:
        """Returns the local sidereal time for a given time.

        Args:
            time: Time to convert to LST.

        Returns:
            Local sidereal time.
        """

        # no location
        if not isinstance(self._location, EarthLocation):
            raise ValueError("No location given.")

        # convert to Time
        if not isinstance(time, Time):
            time = Time(time)
        # return LST
        return time.sidereal_time("mean", longitude=self._location.lon)

    @functools.lru_cache()
    def zenith_position(self, lst: Longitude) -> SkyCoord:
        """Returns the RA/Dec position of the zenith.

        Args:
            lst: Local sidereal time to use.

        Returns:
            SkyCoord with current zenith position.
        """
        if not isinstance(self._location, EarthLocation):
            raise ValueError("No location given.")
        return SkyCoord(lst, self._location.lat, frame=ICRS)

    def now(self) -> Time:
        """Returns current time."""
        return Time.now()

    def to_altaz(self, radec: SkyCoord, time: Optional[Time] = None) -> SkyCoord:
        """Converts a given set of RA/Dec to Alt/Az for the current location at a given time.

        Args:
            radec: RA/Dec coordinates to convert.
            time: Time to use, or none for now.

        Returns:
            Alt/Az coordinates for given RA/Dec.
        """
        if time is None:
            time = Time.now()
        return radec.transform_to(AltAz(obstime=time, location=self.location))

    def to_radec(self, altaz: SkyCoord, time: Optional[Time] = None) -> SkyCoord:
        """Converts a given set of Alt/Az to RA/Dec for the current location at a given time.

        Args:
            altaz: Alt/Az coordinates to convert.
            time: Time to use, or none for now.

        Returns:
            RA/Dec coordinates for given Alt/Az.
        """
        if time is None:
            time = Time.now()
        altaz.location = self.location
        altaz.obstime = time
        return altaz.icrs

    @functools.lru_cache()
    def sun(self, time: Time, altaz: bool = True) -> SkyCoord:
        """Returns the position of the sun, either as RA/Dec or Alt/Az for the given time.

        Args:
            time: Time to calculate position for.
            altaz: If True, Alt/Az is returned, otherwise RA/Dec.

        Returns:
            Coordinates of sun.
        """

        # alt/az or ra/dec?
        if altaz:
            return self.to_altaz(get_sun(time), time)
        else:
            return get_sun(time)


__all__ = ["Environment"]
