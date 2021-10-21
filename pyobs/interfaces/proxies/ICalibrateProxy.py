import typing

from pyobs.utils.threads import Future
from .interfaceproxy import InterfaceProxy


class ICalibrateProxy(InterfaceProxy):
    def calibrate(self) -> Future[None]:
        ...

