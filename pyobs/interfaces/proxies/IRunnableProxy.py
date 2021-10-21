import typing

from pyobs.utils.threads import Future
from .IAbortableProxy import IAbortableProxy
from .InterfaceProxy import InterfaceProxy


class IRunnableProxy(IAbortableProxy, InterfaceProxy):
    def abort(self) -> Future[None]:
        ...

    def run(self) -> Future[None]:
        ...

