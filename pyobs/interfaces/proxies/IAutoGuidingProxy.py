from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from pyobs.utils.threads import Future
from .IStartStopProxy import IStartStopProxy
from .IRunningProxy import IRunningProxy
from .interfaceproxy import InterfaceProxy


class IAutoGuidingProxy(IStartStopProxy, IRunningProxy, InterfaceProxy):
    def is_running(self) -> 'Future[bool]':
        ...

    def set_exposure_time(self, exposure_time: float) -> 'Future[None]':
        ...

    def start(self) -> 'Future[None]':
        ...

    def stop(self) -> 'Future[None]':
        ...

