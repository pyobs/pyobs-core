import typing

from pyobs.utils.threads import Future
from .interfaceproxy import InterfaceProxy


class IOffsetsRaDecProxy(InterfaceProxy):
    def get_offsets_radec(self) -> Future[typing.Tuple[float, float]]:
        ...

    def set_offsets_radec(self, dra: float, ddec: float) -> Future[None]:
        ...

