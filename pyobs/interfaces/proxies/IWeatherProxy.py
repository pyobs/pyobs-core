import typing

from pyobs.utils.threads import Future
from pyobs.utils.enums import WeatherSensors
from .InterfaceProxy import InterfaceProxy


class IWeatherProxy(InterfaceProxy):
    def get_current_weather(self) -> Future[dict]:
        ...

    def get_sensor_value(self, station: str, sensor: WeatherSensors) -> Future[typing.Tuple[str, float]]:
        ...

    def get_weather_status(self) -> Future[dict]:
        ...

    def is_weather_good(self) -> Future[bool]:
        ...

