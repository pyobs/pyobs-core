import typing

from pyobs.utils.threads import Future
from .InterfaceProxy import InterfaceProxy


class IModuleProxy(InterfaceProxy):
    def label(self) -> Future[str]:
        ...

