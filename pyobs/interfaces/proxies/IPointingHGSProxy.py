import typing

from pyobs.utils.threads import Future
from .interfaceproxy import InterfaceProxy


class IPointingHGSProxy(InterfaceProxy):
    def get_hgs_lon_lat(self) -> Future[typing.Tuple[float, float]]:
        ...

    def move_hgs_lon_lat(self, lon: float, lat: float) -> Future[None]:
        ...

