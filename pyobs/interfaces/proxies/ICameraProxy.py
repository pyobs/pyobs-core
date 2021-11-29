from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from pyobs.utils.threads import Future
from pyobs.utils.enums import ExposureStatus
from .IAbortableProxy import IAbortableProxy
from .IImageGrabberProxy import IImageGrabberProxy
from .interfaceproxy import InterfaceProxy


class ICameraProxy(IAbortableProxy, IImageGrabberProxy, InterfaceProxy):
    __module__ = 'pyobs.interfaces.proxies'

    def abort(self) -> 'Future[None]':
        ...

    def get_exposure_progress(self) -> 'Future[float]':
        ...

    def get_exposure_status(self) -> 'Future[ExposureStatus]':
        ...

    def grab_image(self, broadcast: bool = True) -> 'Future[str]':
        ...

