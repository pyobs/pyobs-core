import typing

from pyobs.utils.threads import Future
from .IStartStopProxy import IStartStopProxy
from .IRunningProxy import IRunningProxy
from .InterfaceProxy import InterfaceProxy


class IAutonomousProxy(IStartStopProxy, IRunningProxy, InterfaceProxy):
    def is_running(self) -> Future[bool]:
        ...

    def start(self) -> Future[None]:
        ...

    def stop(self) -> Future[None]:
        ...

