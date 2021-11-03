import typing

from pyobs.utils.threads import Future
from .interfaceproxy import InterfaceProxy


class IBinningProxy(InterfaceProxy):
    def get_binning(self) -> Future[typing.Tuple[int, int]]:
        ...

    def list_binnings(self) -> Future[typing.List[typing.Tuple[int, int]]]:
        ...

    def set_binning(self, x: int, y: int) -> Future[None]:
        ...

