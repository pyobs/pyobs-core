from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from pyobs.utils.threads import Future
from pyobs.utils.enums import WeatherSensors
from .IStartStopProxy import IStartStopProxy
from .IRunningProxy import IRunningProxy
from .interfaceproxy import InterfaceProxy


class IWeatherProxy(IStartStopProxy, IRunningProxy, InterfaceProxy):
    __module__ = 'pyobs.interfaces.proxies'

    def get_current_weather(self) -> 'Future[typing.Dict[str, typing.Any]]':
        ...

    def get_sensor_value(self, station: str, sensor: WeatherSensors) -> 'Future[typing.Tuple[str, float]]':
        ...

    def get_weather_status(self) -> 'Future[typing.Dict[str, typing.Any]]':
        ...

    def is_running(self) -> 'Future[bool]':
        ...

    def is_weather_good(self) -> 'Future[bool]':
        ...

    def start(self) -> 'Future[None]':
        ...

    def stop(self) -> 'Future[None]':
        ...

