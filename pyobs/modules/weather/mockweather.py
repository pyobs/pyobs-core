from __future__ import annotations

from typing import Any

from pyobs.events import BadWeatherEvent, GoodWeatherEvent
from pyobs.interfaces import FitsHeaderEntry, IFitsHeaderBefore, IRunning, IWeather, WeatherSensorReading, WeatherState
from pyobs.interfaces.IRunning import RunningState
from pyobs.modules import Module
from pyobs.modules.weather.weather import FITS_HEADERS, SENSOR_UNITS
from pyobs.utils import exceptions as exc
from pyobs.utils.enums import WeatherSensors

DEFAULT_SENSOR_VALUES: dict[WeatherSensors, float] = {
    WeatherSensors.TEMPERATURE: 15.0,
    WeatherSensors.HUMIDITY: 40.0,
    WeatherSensors.PRESSURE: 1013.0,
    WeatherSensors.WINDDIR: 180.0,
    WeatherSensors.WINDSPEED: 5.0,
    WeatherSensors.RAIN: 0.0,
    WeatherSensors.SKYTEMP: -20.0,
    WeatherSensors.DEWPOINT: 2.0,
    WeatherSensors.PARTICLES: 0.0,
    WeatherSensors.SKYMAG: 21.5,
}


class MockWeather(Module, IWeather, IFitsHeaderBefore):
    """A mock weather station for testing and simulations."""

    __module__ = "pyobs.modules.weather"

    def __init__(self, good: bool = True, sensors: dict[str, float] | None = None, **kwargs: Any):
        """Creates a new mock weather station.

        Args:
            good: Initial weather-good state.
            sensors: Initial sensor values, keyed by sensor value (e.g. "temp", "humid"), overriding the defaults.
        """
        Module.__init__(self, **kwargs)

        self._good = good
        self._active = True
        self._sensors: dict[WeatherSensors, float] = dict(DEFAULT_SENSOR_VALUES)
        if sensors:
            for key, value in sensors.items():
                self._sensors[WeatherSensors(key)] = value

    async def open(self) -> None:
        """Open module."""
        await Module.open(self)

        if self._comm:
            await self.comm.register_event(BadWeatherEvent)
            await self.comm.register_event(GoodWeatherEvent)

        await self._publish_state()

    async def start(self, **kwargs: Any) -> None:
        """Starts a service."""

        # did status change and weather is now bad?
        if not self._active and not self._good:
            await self.comm.send_event(BadWeatherEvent())

        self._active = True
        await self._publish_state()

    async def stop(self, **kwargs: Any) -> None:
        """Stops a service."""
        self._active = False
        await self._publish_state()

    async def is_running(self, **kwargs: Any) -> bool:
        """Whether a service is running."""
        return self._active

    async def set_good(self, good: bool) -> None:
        """Set the simulated weather-good state, for use in tests and simulations.

        Fires a GoodWeatherEvent/BadWeatherEvent on change, and publishes the updated state.

        Args:
            good: New weather-good state.
        """
        if good == self._good:
            return

        self._good = good
        if self._active:
            await self.comm.send_event(GoodWeatherEvent() if good else BadWeatherEvent())

        await self._publish_state()

    def set_sensor_value(self, sensor: WeatherSensors, value: float) -> None:
        """Set a simulated sensor's value, for use in tests and simulations.

        Args:
            sensor: Sensor to set.
            value: New value.
        """
        self._sensors[sensor] = value

    async def _publish_state(self) -> None:
        is_good = True if not self._active else self._good
        await self.comm.set_state(IWeather, WeatherState(good=is_good, readings=self._get_readings()))
        await self.comm.set_state(IRunning, RunningState(running=self._active))

    def _get_readings(self) -> list[WeatherSensorReading]:
        return [
            WeatherSensorReading(sensor=sensor, value=value, unit=SENSOR_UNITS[sensor])
            for sensor, value in self._sensors.items()
        ]

    async def get_sensor_value(self, station: str, sensor: WeatherSensors, **kwargs: Any) -> WeatherSensorReading:
        """Return value for given sensor.

        Args:
            station: Name of weather station to get value from (ignored, there is only one simulated station).
            sensor: Name of sensor to get value from.

        Returns:
            Current reading for the given sensor.

        Raises:
            InvalidArgumentError: If sensor is unknown.
        """
        if sensor not in self._sensors:
            raise exc.InvalidArgumentError(f"Unknown sensor: {sensor}")

        return WeatherSensorReading(sensor=sensor, value=self._sensors[sensor], unit=SENSOR_UNITS[sensor])

    async def get_fits_header_before(
        self, namespaces: list[str] | None = None, **kwargs: Any
    ) -> dict[str, FitsHeaderEntry]:
        """Returns FITS header for the current status of this module.

        Args:
            namespaces: If given, only return FITS headers for the given namespaces.

        Returns:
            Dictionary containing FITS headers.
        """
        header = {}
        for sensor, value in self._sensors.items():
            key, comment, dtype = FITS_HEADERS[sensor]
            header[key] = FitsHeaderEntry(dtype(value), comment)
        return header


__all__ = ["MockWeather"]
