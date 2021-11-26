from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from pyobs.utils.threads import Future
from .interfaceproxy import InterfaceProxy


class IRunningProxy(InterfaceProxy):
    __module__ = 'pyobs.interfaces.proxies'

    def is_running(self) -> 'Future[bool]':
        ...

