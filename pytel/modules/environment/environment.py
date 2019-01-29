import datetime
import functools
import logging
from typing import Union

import pytz
from astropy.coordinates import EarthLocation, Longitude, SkyCoord, ICRS, get_sun, AltAz
#from astropy.time import Time
from pytel.utils.time import Time

from pytel import PytelModule


log = logging.getLogger(__name__)


class Environment(PytelModule):
    def __init__(self, timezone: str = 'utc', location: Union[dict, EarthLocation] = None, *args, **kwargs):
        PytelModule.__init__(self, *args, **kwargs)

        # get timezone
        self._timezone = pytz.timezone(timezone)
        log.info('Using timezone %s.', timezone)

        # get location
        self._location = None
        if location is not None:
            if isinstance(location, EarthLocation):
                # store directly
                self._location = location
            elif isinstance(location, dict):
                # dictionary?
                if 'longitude' in location and location['longitude'] is not None and \
                        'latitude' in location and location['latitude'] is not None and \
                        'elevation' in location and location['elevation'] is not None:
                    self._location = EarthLocation(location['longitude'], location['latitude'], location['elevation'])
                else:
                    log.error('Location must be provided as dict of longitude/latitude/elevation values.')
            else:
                # nothing
                log.error('Could not initialize location.')
        if self._location is not None:
            log.info('Setting location to longitude=%s, latitude=%s, and elevation=%s.',
                     self._location.lon, self._location.lat, self._location.height)

    @property
    def timezone(self) -> pytz.timezone:
        return self._timezone

    @property
    def location(self):
        return self._location

    @functools.lru_cache()
    def localtime(self, utc: datetime.datetime = None):
        # get UTC
        if utc is None:
            utc = datetime.datetime.utcnow()
        # mark as UTC
        utc_dt = pytz.utc.localize(utc)
        # convert to local timezone
        return utc_dt.astimezone(self._timezone)

    @functools.lru_cache()
    def night_obs(self, time: Union[datetime.datetime, Time]) -> datetime.date:
        # convert to Time
        if isinstance(time, Time):
            time = time.datetime
        # get local datetime
        utc_dt = pytz.utc.localize(time)
        loc_dt = utc_dt.astimezone(self._timezone)
        # get night
        if loc_dt.hour < 15:
            loc_dt += datetime.timedelta(days=-1)
        return loc_dt.date()

    @functools.lru_cache()
    def lst(self, time: Union[datetime.datetime, Time]) -> Longitude:
        # convert to Time
        if not isinstance(time, Time):
            time = Time(time)
        # return LST
        return time.sidereal_time('mean', longitude=self._location.lon)

    @functools.lru_cache()
    def zenith_position(self, lst: Longitude) -> SkyCoord:
        # return zenith position
        return SkyCoord(lst, self._location.lat, frame=ICRS)

    @functools.lru_cache()
    def to_altaz(self, coords: SkyCoord, time: Time):
        return coords.transform_to(AltAz(obstime=time, location=self.location))

    @functools.lru_cache()
    def sun(self, time: Time, altaz=True):
        # alt/az or ra/dec?
        if altaz:
            return self.to_altaz(get_sun(time), time)
        else:
            return get_sun(time)


__all__ = ['Environment']
