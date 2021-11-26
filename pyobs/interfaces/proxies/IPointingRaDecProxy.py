from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from pyobs.utils.threads import Future
from .interfaceproxy import InterfaceProxy


class IPointingRaDecProxy(InterfaceProxy):
    def get_radec(self) -> 'Future[typing.Tuple[float, float]]':
        ...

    def move_radec(self, ra: float, dec: float) -> 'Future[None]':
        ...

