import logging
import requests
import urllib.parse
import json
from typing import Union

from pyobs.events import BadWeatherEvent, GoodWeatherEvent
from pyobs.interfaces import IWeather
from pyobs import PyObsModule


log = logging.getLogger(__name__)


class Weather(PyObsModule, IWeather):
    """Connection to pyobs-weather."""

    def __init__(self, url: str = None, *args, **kwargs):
        """Initialize a new pyobs-weather connector."""
        PyObsModule.__init__(self, *args, **kwargs)

        # store url and create session
        self._url = url
        self._session = requests.session()

        # current status
        self._is_good = None

        # add thread func
        self._add_thread_func(self._update, True)

    def open(self):
        """Open module."""
        PyObsModule.open(self)

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

            except (requests.exceptions.Timeout, ValueError) as e:
                # on error, we're always bad
                log.error('Request failed: %s', e)
                is_good = False
                error = True

            # did status change?
            if is_good != self._is_good:
                if is_good:
                    self.comm.send_event(GoodWeatherEvent())
                else:
                    self.comm.send_event(BadWeatherEvent())
                self._is_good = is_good

            # sleep a little
            self.closing.wait(60 if error else 5)

    def get_weather_status(self, *args, **kwargs) -> dict:
        """Returns status of object in form of a dictionary. See other interfaces for details."""
        raise NotImplementedError

    def is_weather_good(self, *args, **kwargs) -> bool:
        """Whether the weather is good to observe."""
        return False if self._is_good is None else self._is_good

    def get_sensor_value(self, station: str, sensor: IWeather.Sensors, *args, **kwargs) \
            -> (Union[float, None], Union[str, None]):
        """Return value for given sensor.

        Args:
            station: Name of weather station to get value from.
            sensor: Name of sensor to get value from.

        Returns:
            Tuple of current value of given sensor or None and time of measurement or None.
        """

        # do request
        res = self._session.get(urllib.parse.urljoin(self._url, 'api/stations/%s/%s/' % (station, sensor.value)))
        if res.status_code != 200:
            raise ValueError('Could not connect to weather station.')

        # to json
        status = res.json()
        if 'time' not in status or 'value' not in status:
            raise ValueError('Time and/or value parameters not found in response from weather station.')

        # return time and valie
        return status['time'], status['value']


__all__ = ['Weather']
