import typing

from pyobs.utils.threads import Future
from .IAbortableProxy import IAbortableProxy
from .InterfaceProxy import InterfaceProxy


class IFlatFieldProxy(IAbortableProxy, InterfaceProxy):
    def abort(self) -> Future[None]:
        ...

    def flat_field(self, count: int = 20) -> Future[typing.Tuple[int, float]]:
        ...

