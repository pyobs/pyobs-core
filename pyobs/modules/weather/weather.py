import logging
from typing import Tuple, Any, Dict, List

import requests
import urllib.parse
import threading
import astropy.units as u

from pyobs.utils.enums import WeatherSensors
from pyobs.utils.time import Time
from pyobs.events import BadWeatherEvent, GoodWeatherEvent
from pyobs.interfaces import IWeather, IFitsHeaderBefore
from pyobs.modules import Module


log = logging.getLogger(__name__)


FITS_HEADERS = {
    WeatherSensors.TEMPERATURE: ('WS-TEMP', 'Ambient temperature average during exposure, C', float),
    WeatherSensors.HUMIDITY: ('WS-HUMID', 'Ambient rel. humidity average, %', float),
    WeatherSensors.PRESSURE: ('WS-PRESS', 'Average atmospheric pressure, hPa', float),
    WeatherSensors.WINDDIR: ('WS-AZ', 'Average wind direction, not corrected for overlap, deg', float),
    WeatherSensors.WINDSPEED: ('WS-WIND', 'Ambient average wind speed, km/h', float),
    WeatherSensors.RAIN: ('WS-PREC', 'Ambient precipitation [0/1]', bool),
    WeatherSensors.SKYTEMP: ('WS-SKY', 'Average sky temperature, C', float),
    WeatherSensors.DEWPOINT: ('WS-TDEW', 'Ambient dewpoint average during expsoure, C', float),
    WeatherSensors.PARTICLES: ('WS-DUST', 'Average particle count during exposure, ppcm', float)
}


class Weather(Module, IWeather, IFitsHeaderBefore):
    """Connection to pyobs-weather."""
    __module__ = 'pyobs.modules.weather'

    def __init__(self, url: str, system_init_time: int = 300, **kwargs: Any):
        """Initialize a new pyobs-weather connector.

        Args:
            url: URL to weather station
            system_init_time: Time in seconds the full system needs to initialize
        """
        Module.__init__(self, **kwargs)

        # store and create session
        self._system_init_time = system_init_time
        self._url = url
        self._session = requests.session()

        # current status
        self._is_good = None

        # whole status
        self._status: Dict[str, Any] = {}
        self._status_lock = threading.RLock()

        # add thread func
        self.add_thread_func(self._update, True)

    def open(self):
        """Open module."""
        Module.open(self)

        # subscribe to events
        if self.comm:
            self.comm.register_event(BadWeatherEvent)
            self.comm.register_event(GoodWeatherEvent)

    def _update(self):
        """Update weather info."""

        # loop forever
        while not self.closing.is_set():
            # new is_good status
            is_good = None
            error = False

            try:
                # fetch status
                res = self._session.get(urllib.parse.urljoin(self._url, 'api/current/'), timeout=5)
                if res.status_code != 200:
                    raise ValueError('Could not connect to weather station.')

                # to json
                status = res.json()
                if 'good' not in status:
                    raise ValueError('Good parameter not found in response from weather station.')

                # store it
                is_good = status['good']
                with self._status_lock:
                    self._status = status

            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError, ValueError) as e:
                # on error, we're always bad
                log.error('Request failed: %s', e)
                is_good = False
                error = True

            # did status change?
            if is_good != self._is_good:
                if is_good:
                    log.info(('Weather is now good.'))
                    eta = Time.now() + self._system_init_time * u.second
                    self.comm.send_event(GoodWeatherEvent(eta=eta))
                else:
                    log.info('Weather is now bad.')
                    self.comm.send_event(BadWeatherEvent())
                self._is_good = is_good

            # sleep a little
            self.closing.wait(60 if error else 5)

    def get_weather_status(self, **kwargs: Any) -> dict:
        """Returns status of object in form of a dictionary. See other interfaces for details."""
        raise NotImplementedError

    def is_weather_good(self, **kwargs: Any) -> bool:
        """Whether the weather is good to observe."""
        return False if self._is_good is None else self._is_good

    def get_current_weather(self, **kwargs: Any) -> dict:
        """Returns current weather.

        Returns:
            Dictionary containing entries for time, good, and sensor, with the latter being another dictionary
            with sensor information, which contain a value and a good flag.
        """
        with self._status_lock:
            return self._status

    def get_sensor_value(self, station: str, sensor: WeatherSensors, **kwargs: Any) -> Tuple[str, float]:
        """Return value for given sensor.

        Args:
            station: Name of weather station to get value from.
            sensor: Name of sensor to get value from.

        Returns:
            Tuple of current value of given sensor or None and time of measurement or None.
        """

        # do request
        url = urllib.parse.urljoin(self._url, 'api/stations/%s/%s/' % (station, sensor.value))
        res = self._session.get(url)
        if res.status_code != 200:
            raise ValueError('Could not connect to weather station.')

        # to json
        status = res.json()
        if 'time' not in status or 'value' not in status:
            raise ValueError('Time and/or value parameters not found in response from weather station.')

        # return time and value
        return status['time'], status['value']

    def get_fits_header_before(self, namespaces: List[str] = None, **kwargs: Any) -> Dict[str, Tuple[Any, str]]:
        """Returns FITS header for the current status of this module.

        Args:
            namespaces: If given, only return FITS headers for the given namespaces.

        Returns:
            Dictionary containing FITS headers.
        """

        # copy status
        with self._status_lock:
            status = dict(self._status)

        # got sensors?
        if 'sensors' not in status:
            log.error('No sensor data found in status.')
            return {}
        sensors = status['sensors']

        # loop sensor types
        header = {}
        for sensor_type in WeatherSensors:
            # got a value for this type?
            if sensor_type.value in sensors:
                # get value
                if 'value' not in sensors[sensor_type.value]:
                    continue
                value = sensors[sensor_type.value]['value']

                # get header keyword, comment and data type
                key, comment, dtype = FITS_HEADERS[sensor_type]

                # set it
                header[key] = (None if value is None else dtype(value), comment)

        # finished
        return header


__all__ = ['Weather']
