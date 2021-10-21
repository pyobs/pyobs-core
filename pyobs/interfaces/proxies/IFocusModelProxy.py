import typing

from pyobs.utils.threads import Future
from .interfaceproxy import InterfaceProxy


class IFocusModelProxy(InterfaceProxy):
    def get_optimal_focus(self) -> Future[float]:
        ...

    def set_optimal_focus(self) -> Future[None]:
        ...

