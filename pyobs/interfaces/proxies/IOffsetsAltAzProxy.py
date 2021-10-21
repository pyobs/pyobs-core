import typing

from pyobs.utils.threads import Future
from .interfaceproxy import InterfaceProxy


class IOffsetsAltAzProxy(InterfaceProxy):
    def get_offsets_altaz(self) -> Future[typing.Tuple[float, float]]:
        ...

    def set_offsets_altaz(self, dalt: float, daz: float) -> Future[None]:
        ...

