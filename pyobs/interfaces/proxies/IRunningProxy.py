import typing

from pyobs.utils.threads import Future
from .InterfaceProxy import InterfaceProxy


class IRunningProxy(InterfaceProxy):
    def is_running(self) -> Future[bool]:
        ...

