import typing

from pyobs.utils.threads import Future
from .IAbortableProxy import IAbortableProxy
from .InterfaceProxy import InterfaceProxy


class IAutoFocusProxy(IAbortableProxy, InterfaceProxy):
    def abort(self) -> Future[None]:
        ...

    def auto_focus(self, count: int, step: float, exposure_time: float) -> Future[typing.Tuple[float, float]]:
        ...

    def auto_focus_status(self) -> Future[dict]:
        ...

