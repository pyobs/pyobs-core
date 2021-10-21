import typing

from pyobs.utils.threads import Future
from .InterfaceProxy import InterfaceProxy


class IAbortableProxy(InterfaceProxy):
    def abort(self) -> Future[None]:
        ...

