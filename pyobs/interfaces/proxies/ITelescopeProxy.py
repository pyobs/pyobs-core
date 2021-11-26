from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from pyobs.utils.threads import Future
from pyobs.utils.enums import MotionStatus
from .IMotionProxy import IMotionProxy
from .IReadyProxy import IReadyProxy
from .IPointingAltAzProxy import IPointingAltAzProxy
from .IPointingRaDecProxy import IPointingRaDecProxy
from .interfaceproxy import InterfaceProxy


class ITelescopeProxy(IMotionProxy, IReadyProxy, IPointingAltAzProxy, IPointingRaDecProxy, InterfaceProxy):
    def get_altaz(self) -> 'Future[typing.Tuple[float, float]]':
        ...

    def get_motion_status(self, device: typing.Optional[str] = None) -> 'Future[MotionStatus]':
        ...

    def get_radec(self) -> 'Future[typing.Tuple[float, float]]':
        ...

    def init(self) -> 'Future[None]':
        ...

    def is_ready(self) -> 'Future[bool]':
        ...

    def move_altaz(self, alt: float, az: float) -> 'Future[None]':
        ...

    def move_radec(self, ra: float, dec: float) -> 'Future[None]':
        ...

    def park(self) -> 'Future[None]':
        ...

    def stop_motion(self, device: typing.Optional[str] = None) -> 'Future[None]':
        ...

