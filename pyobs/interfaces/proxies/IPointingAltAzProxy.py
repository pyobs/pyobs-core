import typing

from pyobs.utils.threads import Future
from .InterfaceProxy import InterfaceProxy


class IPointingAltAzProxy(InterfaceProxy):
    def get_altaz(self) -> Future[typing.Tuple[float, float]]:
        ...

    def move_altaz(self, alt: float, az: float) -> Future[None]:
        ...

