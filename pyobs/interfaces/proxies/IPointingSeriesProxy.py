import typing

from pyobs.utils.threads import Future
from .interfaceproxy import InterfaceProxy


class IPointingSeriesProxy(InterfaceProxy):
    def add_pointing_measure(self) -> Future[None]:
        ...

    def start_pointing_series(self) -> Future[str]:
        ...

    def stop_pointing_series(self) -> Future[None]:
        ...

