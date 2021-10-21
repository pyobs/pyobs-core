import typing

from pyobs.utils.threads import Future
from .IRunningProxy import IRunningProxy
from .InterfaceProxy import InterfaceProxy


class IAcquisitionProxy(IRunningProxy, InterfaceProxy):
    def acquire_target(self) -> Future[dict]:
        ...

    def is_running(self) -> Future[bool]:
        ...

