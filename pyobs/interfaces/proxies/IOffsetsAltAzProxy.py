from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from pyobs.utils.threads import Future
from .interfaceproxy import InterfaceProxy


class IOffsetsAltAzProxy(InterfaceProxy):
    __module__ = 'pyobs.interfaces.proxies'

    def get_offsets_altaz(self) -> 'Future[typing.Tuple[float, float]]':
        ...

    def set_offsets_altaz(self, dalt: float, daz: float) -> 'Future[None]':
        ...

