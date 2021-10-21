import typing

from pyobs.utils.threads import Future
from .interfaceproxy import InterfaceProxy


class IModuleProxy(InterfaceProxy):
    def label(self) -> Future[str]:
        ...

