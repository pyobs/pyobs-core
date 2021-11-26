from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from pyobs.utils.threads import Future
from .IStartStopProxy import IStartStopProxy
from .IRunningProxy import IRunningProxy
from .interfaceproxy import InterfaceProxy


class IAutonomousProxy(IStartStopProxy, IRunningProxy, InterfaceProxy):
    __module__ = 'pyobs.interfaces.proxies'

    def is_running(self) -> 'Future[bool]':
        ...

    def start(self) -> 'Future[None]':
        ...

    def stop(self) -> 'Future[None]':
        ...

