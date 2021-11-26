from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from pyobs.utils.threads import Future
from .IAbortableProxy import IAbortableProxy
from .interfaceproxy import InterfaceProxy


class IFlatFieldProxy(IAbortableProxy, InterfaceProxy):
    __module__ = 'pyobs.interfaces.proxies'

    def abort(self) -> 'Future[None]':
        ...

    def flat_field(self, count: int = 20) -> 'Future[typing.Tuple[int, float]]':
        ...

