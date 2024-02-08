import asyncio
import logging
from typing import Tuple, Any, Dict, List, Optional

import astropy.units as u

from pyobs.events import BadWeatherEvent, GoodWeatherEvent
from pyobs.interfaces import IWeather, IFitsHeaderBefore
from pyobs.modules import Module
from pyobs.modules.weather.weather_api import WeatherApi
from pyobs.modules.weather.weather_state import WeatherState
from pyobs.utils.enums import WeatherSensors
from pyobs.utils.time import Time

log = logging.getLogger(__name__)


FITS_HEADERS = {
    WeatherSensors.TEMPERATURE: ("WS-TEMP", "Ambient temperature average during exposure, C", float),
    WeatherSensors.HUMIDITY: ("WS-HUMID", "Ambient rel. humidity average, %", float),
    WeatherSensors.PRESSURE: ("WS-PRESS", "Average atmospheric pressure, hPa", float),
    WeatherSensors.WINDDIR: ("WS-AZ", "Average wind direction, not corrected for overlap, deg", float),
    WeatherSensors.WINDSPEED: ("WS-WIND", "Ambient average wind speed, km/h", float),
    WeatherSensors.RAIN: ("WS-PREC", "Ambient precipitation [0/1]", bool),
    WeatherSensors.SKYTEMP: ("WS-SKY", "Average sky temperature, C", float),
    WeatherSensors.DEWPOINT: ("WS-TDEW", "Ambient dewpoint average during expsoure, C", float),
    WeatherSensors.PARTICLES: ("WS-DUST", "Average particle count during exposure, ppcm", float),
    WeatherSensors.SKYMAG: ("SKYMAG", "Sky brightness, mag/arcsec^2", float),
}


class Weather(Module, IWeather, IFitsHeaderBefore):
    """Connection to pyobs-weather."""

    __module__ = "pyobs.modules.weather"

    def __init__(self, url: str, system_init_time: int = 300, **kwargs: Any):
        """Initialize a new pyobs-weather connector.

        Args:
            url: URL to weather station
            system_init_time: Time in seconds the full system needs to initialize
        """
        Module.__init__(self, **kwargs)

        # store and create session
        self._system_init_time = system_init_time
        self._api = WeatherApi(url)

        # whether module is active, i.e. if None, weather is always good
        self._active = True

        # current status
        self._is_good: Optional[bool] = None

        # whole status
        self._weather = WeatherState()

        # add thread func
        self.add_background_task(self._update, True)


    async def open(self) -> None:
        """Open module."""
        await Module.open(self)

        # subscribe to events
        if self.comm:
            await self.comm.register_event(BadWeatherEvent)
            await self.comm.register_event(GoodWeatherEvent)

    async def start(self, **kwargs: Any) -> None:
        """Starts a service."""

        # did status change and weather is now bad?
        if not self._active and not self._is_good:
            # send event!
            await self.comm.send_event(BadWeatherEvent())

        # activate
        self._active = True

    async def stop(self, **kwargs: Any) -> None:
        """Stops a service."""
        self._active = False

    async def is_running(self, **kwargs: Any) -> bool:
        """Whether a service is running."""
        return self._active

    async def _run(self) -> None:
        while True:
            await self._loop()

    async def _loop(self) -> None:
        try:
            await self._update()
        except:
            sleep = 60
        else:
            sleep = 5

        await asyncio.sleep(sleep)

    async def _update(self) -> None:
        """Update weather info."""

        was_good = self._weather.is_good

        try:
            self._weather.status = await self._api.get_current_status()
        except Exception as e:
            log.warning("Request failed: %s", str(e))
            self._weather.is_good = False   # on error, we're always bad

        if was_good != self._weather.is_good and self._active:
            if self._weather.is_good:
                log.info("Weather is now good.")
                eta = self._calc_system_init_eta()
                await self.comm.send_event(GoodWeatherEvent(eta=eta))
            else:
                log.info("Weather is now bad.")
                await self.comm.send_event(BadWeatherEvent())

    def _calc_system_init_eta(self) -> Time:
        return Time.now() + self._system_init_time * u.second

    async def get_weather_status(self, **kwargs: Any) -> Dict[str, Any]:
        """Returns status of object in form of a dictionary. See other interfaces for details."""
        raise NotImplementedError

    async def is_weather_good(self, **kwargs: Any) -> bool:
        """Whether the weather is good to observe."""

        # if not active, weather is always good
        if not self._active:
            return True

        # otherwise it depends on the is_good flag
        return False if self._is_good is None else self._is_good

    async def get_current_weather(self, **kwargs: Any) -> Dict[str, Any]:
        """Returns current weather.

        Returns:
            Dictionary containing entries for time, good, and sensor, with the latter being another dictionary
            with sensor information, which contain a value and a good flag.
        """
        return self._weather.status

    async def get_sensor_value(self, station: str, sensor: WeatherSensors, **kwargs: Any) -> Tuple[str, float]:
        """Return value for given sensor.

        Args:
            station: Name of weather station to get value from.
            sensor: Name of sensor to get value from.

        Returns:
            Tuple of current value of given sensor or None and time of measurement or None.
        """

        # do request
        status = await self._api.get_sensor_value(station, sensor)

        # to json
        if "time" not in status or "value" not in status:
            raise ValueError("Time and/or value parameters not found in response from weather station.")

        # return time and value
        return status["time"], status["value"]

    async def get_fits_header_before(
        self, namespaces: Optional[List[str]] = None, **kwargs: Any
    ) -> Dict[str, Tuple[Any, str]]:
        """Returns FITS header for the current status of this module.

        Args:
            namespaces: If given, only return FITS headers for the given namespaces.

        Returns:
            Dictionary containing FITS headers.
        """

        if "sensors" not in self._weather.status:
            log.error("No sensor data found in status.")
            return {}
        sensors = self._weather.status["sensors"]

        sensor_types = [sensor_type for sensor_type in WeatherSensors if sensor_type.value in sensors]
        valid_sensor_types = [sensor_type for sensor_type in sensor_types if "value" in sensors[sensor_type.value]]

        header = {}
        for sensor_type in valid_sensor_types:
            value = sensors[sensor_type.value]["value"]

            key, comment, dtype = FITS_HEADERS[sensor_type]

            header_value = None if value is None else dtype(value)
            header[key] = (header_value, comment)

        return header


__all__ = ["Weather"]
