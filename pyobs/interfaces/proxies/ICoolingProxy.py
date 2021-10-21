import typing

from pyobs.utils.threads import Future
from .ITemperaturesProxy import ITemperaturesProxy
from .InterfaceProxy import InterfaceProxy


class ICoolingProxy(ITemperaturesProxy, InterfaceProxy):
    def get_cooling_status(self) -> Future[typing.Tuple[bool, float, float]]:
        ...

    def get_temperatures(self) -> Future[typing.Dict[str, float]]:
        ...

    def set_cooling(self, enabled: bool, setpoint: float) -> Future[None]:
        ...

