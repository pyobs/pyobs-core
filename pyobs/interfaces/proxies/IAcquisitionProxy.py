import typing

from pyobs.utils.threads import Future
from .IRunningProxy import IRunningProxy
from .interfaceproxy import InterfaceProxy


class IAcquisitionProxy(IRunningProxy, InterfaceProxy):
    def acquire_target(self) -> Future[typing.Dict[str, typing.Any]]:
        ...

    def is_running(self) -> Future[bool]:
        ...

