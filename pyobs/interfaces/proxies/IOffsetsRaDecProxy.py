from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from pyobs.utils.threads import Future
from .interfaceproxy import InterfaceProxy


class IOffsetsRaDecProxy(InterfaceProxy):
    __module__ = 'pyobs.interfaces.proxies'

    def get_offsets_radec(self) -> 'Future[typing.Tuple[float, float]]':
        ...

    def set_offsets_radec(self, dra: float, ddec: float) -> 'Future[None]':
        ...

