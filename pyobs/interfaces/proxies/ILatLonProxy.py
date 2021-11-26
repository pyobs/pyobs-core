from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from pyobs.utils.threads import Future
from .interfaceproxy import InterfaceProxy


class ILatLonProxy(InterfaceProxy):
    __module__ = 'pyobs.interfaces.proxies'

    def get_latlon(self) -> 'Future[typing.Tuple[float, float]]':
        ...

    def move_latlon(self, lat: float, lon: float) -> 'Future[None]':
        ...

