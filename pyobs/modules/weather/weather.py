from __future__ import annotations

import asyncio
import logging
from typing import Any

import astropy.units as u

from pyobs.events import BadWeatherEvent, GoodWeatherEvent
from pyobs.interfaces import FitsHeaderEntry, IFitsHeaderBefore, IRunning, IWeather, WeatherSensorReading, WeatherState
from pyobs.interfaces.IRunning import RunningState
from pyobs.modules import Module
from pyobs.modules.weather.weather_api import WeatherApi
from pyobs.modules.weather.weather_state import WeatherStatus
from pyobs.utils import exceptions as exc
from pyobs.utils.enums import Unit, WeatherSensors
from pyobs.utils.time import Time

log = logging.getLogger(__name__)


class WeatherResponseError(exc.PyobsError):
    """The weather station's API response was malformed or incomplete (missing an expected field)
    -- plausibly transient (a flaky station/network), worth retrying, as opposed to a caller
    passing a bad station/sensor name."""

    pass


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

# unit for each sensor's reading in WeatherState.readings -- reuses the canonical Unit enum where one
# applies; RAIN is a 0/1 flag stored as float, interpreted as bool; PARTICLES/SKYMAG have no canonical unit
SENSOR_UNITS = {
    WeatherSensors.TEMPERATURE: Unit.CELSIUS.value,
    WeatherSensors.HUMIDITY: Unit.PERCENT.value,
    WeatherSensors.PRESSURE: Unit.HPA.value,
    WeatherSensors.WINDDIR: Unit.DEGREES.value,
    WeatherSensors.WINDSPEED: Unit.KM_PER_HOUR.value,
    WeatherSensors.RAIN: "bool",
    WeatherSensors.SKYTEMP: Unit.CELSIUS.value,
    WeatherSensors.DEWPOINT: Unit.CELSIUS.value,
    WeatherSensors.PARTICLES: "1/m3",
    WeatherSensors.SKYMAG: "mag/arcsec2",
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

        # raw status from the weather station API
        self._weather = WeatherStatus()

        # add thread func
        self.add_background_task(self._run, True)

    async def open(self) -> None:
        """Open module."""
        await Module.open(self)

        # subscribe to events
        if self._comm:
            await self.comm.register_event(BadWeatherEvent)
            await self.comm.register_event(GoodWeatherEvent)

        await self.comm.set_state(IRunning, RunningState(running=self._active))

    async def start(self, **kwargs: Any) -> None:
        """Starts a service."""

        # did status change and weather is now bad?
        if not self._active and not self._weather.is_good:
            # send event!
            await self.comm.send_event(BadWeatherEvent())

        # activate
        self._active = True
        await self.comm.set_state(IRunning, RunningState(running=self._active))

    async def stop(self, **kwargs: Any) -> None:
        """Stops a service."""
        self._active = False
        await self.comm.set_state(IRunning, RunningState(running=self._active))

    async def is_running(self, **kwargs: Any) -> bool:
        """Whether a service is running."""
        return self._active

    async def _run(self) -> None:
        while True:
            await self._loop()

    async def _loop(self) -> None:
        try:
            await self._update()
        except Exception:
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
            self._weather.is_good = False  # on error, we're always bad

        if was_good != self._weather.is_good and self._active:
            if self._weather.is_good:
                log.info("Weather is now good.")
                eta = self._calc_system_init_eta()
                await self.comm.send_event(GoodWeatherEvent(eta=eta))
            else:
                log.info("Weather is now bad.")
                await self.comm.send_event(BadWeatherEvent())

        # publish state
        is_good = True if not self._active else self._weather.is_good
        await self.comm.set_state(IWeather, WeatherState(good=is_good, readings=self._get_readings()))

    def _get_readings(self) -> list[WeatherSensorReading]:
        """Builds the current per-sensor readings from the last raw status, for state publication."""
        sensors = self._weather.status.get("sensors", {})
        readings = []
        for sensor_type, unit in SENSOR_UNITS.items():
            entry = sensors.get(sensor_type.value)
            if entry is None or entry.get("value") is None:
                continue
            readings.append(WeatherSensorReading(sensor=sensor_type, value=entry["value"], unit=unit))
        return readings

    def _calc_system_init_eta(self) -> Time:
        return Time(Time.now() + self._system_init_time * u.second)

    async def get_sensor_value(self, station: str, sensor: WeatherSensors, **kwargs: Any) -> WeatherSensorReading:
        """Return value for given sensor.

        Args:
            station: Name of weather station to get value from.
            sensor: Name of sensor to get value from.

        Returns:
            Current reading for the given sensor.

        Raises:
            WeatherResponseError: If the weather station's response is malformed.
        """

        # do request
        status = await self._api.get_sensor_value(station, sensor)

        # to json
        if "time" not in status or "value" not in status:
            raise WeatherResponseError("Time and/or value parameters not found in response from weather station.")

        # return reading
        return WeatherSensorReading(
            sensor=sensor,
            value=status["value"],
            unit=SENSOR_UNITS[sensor],
            time=Time(status["time"], format="isot", scale="utc"),
        )

    async def get_fits_header_before(
        self, namespaces: list[str] | None = None, **kwargs: Any
    ) -> dict[str, FitsHeaderEntry]:
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
            header[key] = FitsHeaderEntry(header_value, comment)

        return header


__all__ = ["Weather"]
