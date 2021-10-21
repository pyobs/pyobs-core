import typing

from pyobs.utils.threads import Future
from .interfaceproxy import InterfaceProxy


class IAbortableProxy(InterfaceProxy):
    def abort(self) -> Future[None]:
        ...

