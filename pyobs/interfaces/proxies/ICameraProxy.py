import typing

from pyobs.utils.threads import Future
from pyobs.utils.enums import ExposureStatus
from .IAbortableProxy import IAbortableProxy
from .IImageGrabberProxy import IImageGrabberProxy
from .InterfaceProxy import InterfaceProxy


class ICameraProxy(IAbortableProxy, IImageGrabberProxy, InterfaceProxy):
    def abort(self) -> Future[None]:
        ...

    def expose(self, broadcast: bool = True) -> Future[str]:
        ...

    def get_exposure_progress(self) -> Future[float]:
        ...

    def get_exposure_status(self) -> Future[ExposureStatus]:
        ...

    def grab_image(self, broadcast: bool = True) -> Future[str]:
        ...

