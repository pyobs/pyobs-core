import typing

from pyobs.utils.threads import Future
from pyobs.utils.enums import WeatherSensors
from .interfaceproxy import InterfaceProxy


class IWeatherProxy(InterfaceProxy):
    def get_current_weather(self) -> Future[typing.Dict[str, typing.Any]]:
        ...

    def get_sensor_value(self, station: str, sensor: WeatherSensors) -> Future[typing.Tuple[str, float]]:
        ...

    def get_weather_status(self) -> Future[typing.Dict[str, typing.Any]]:
        ...

    def is_weather_good(self) -> Future[bool]:
        ...

