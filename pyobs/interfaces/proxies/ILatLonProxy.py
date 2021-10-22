import typing

from pyobs.utils.threads import Future
from .interfaceproxy import InterfaceProxy


class ILatLonProxy(InterfaceProxy):
    def get_latlon(self) -> Future[typing.Tuple[float, float]]:
        ...

    def move_latlon(self, lat: float, lon: float) -> Future[None]:
        ...

