import typing

from pyobs.utils.threads import Future
from .interfaceproxy import InterfaceProxy


class IExposureTimeProxy(InterfaceProxy):
    def get_exposure_time(self) -> Future[float]:
        ...

    def get_exposure_time_left(self) -> Future[float]:
        ...

    def set_exposure_time(self, exposure_time: float) -> Future[None]:
        ...

