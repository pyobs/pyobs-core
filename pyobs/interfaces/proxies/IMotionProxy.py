import typing

from pyobs.utils.threads import Future
from pyobs.utils.enums import MotionStatus
from .IReadyProxy import IReadyProxy
from .InterfaceProxy import InterfaceProxy


class IMotionProxy(IReadyProxy, InterfaceProxy):
    def get_motion_status(self, device: typing.Optional[str] = None) -> Future[MotionStatus]:
        ...

    def init(self) -> Future[None]:
        ...

    def is_ready(self) -> Future[bool]:
        ...

    def park(self) -> Future[None]:
        ...

    def stop_motion(self, device: typing.Optional[str] = None) -> Future[None]:
        ...

