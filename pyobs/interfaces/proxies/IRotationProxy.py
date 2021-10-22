import typing

from pyobs.utils.threads import Future
from pyobs.utils.enums import MotionStatus
from .IMotionProxy import IMotionProxy
from .IReadyProxy import IReadyProxy
from .interfaceproxy import InterfaceProxy


class IRotationProxy(IMotionProxy, IReadyProxy, InterfaceProxy):
    def get_motion_status(self, device: typing.Optional[str] = None) -> Future[MotionStatus]:
        ...

    def get_rotation(self) -> Future[float]:
        ...

    def init(self) -> Future[None]:
        ...

    def is_ready(self) -> Future[bool]:
        ...

    def park(self) -> Future[None]:
        ...

    def set_rotation(self, angle: float) -> Future[None]:
        ...

    def stop_motion(self, device: typing.Optional[str] = None) -> Future[None]:
        ...

    def track(self, ra: float, dec: float) -> Future[None]:
        ...

