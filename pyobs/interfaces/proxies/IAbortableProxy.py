from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from pyobs.utils.threads import Future
from .interfaceproxy import InterfaceProxy


class IAbortableProxy(InterfaceProxy):
    __module__ = 'pyobs.interfaces.proxies'

    def abort(self) -> 'Future[None]':
        ...

