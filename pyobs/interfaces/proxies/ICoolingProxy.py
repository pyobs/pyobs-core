from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from pyobs.utils.threads import Future
from .ITemperaturesProxy import ITemperaturesProxy
from .interfaceproxy import InterfaceProxy


class ICoolingProxy(ITemperaturesProxy, InterfaceProxy):
    __module__ = 'pyobs.interfaces.proxies'

    def get_cooling_status(self) -> 'Future[typing.Tuple[bool, float, float]]':
        ...

    def get_temperatures(self) -> 'Future[typing.Dict[str, float]]':
        ...

    def set_cooling(self, enabled: bool, setpoint: float) -> 'Future[None]':
        ...

