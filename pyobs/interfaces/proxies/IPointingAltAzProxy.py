from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from pyobs.utils.threads import Future
from .interfaceproxy import InterfaceProxy


class IPointingAltAzProxy(InterfaceProxy):
    __module__ = 'pyobs.interfaces.proxies'

    def get_altaz(self) -> 'Future[typing.Tuple[float, float]]':
        ...

    def move_altaz(self, alt: float, az: float) -> 'Future[None]':
        ...

