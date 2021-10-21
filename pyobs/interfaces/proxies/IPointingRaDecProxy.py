import typing

from pyobs.utils.threads import Future
from .InterfaceProxy import InterfaceProxy


class IPointingRaDecProxy(InterfaceProxy):
    def get_radec(self) -> Future[typing.Tuple[float, float]]:
        ...

    def move_radec(self, ra: float, dec: float) -> Future[None]:
        ...

