from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from pyobs.utils.threads import Future
from .interfaceproxy import InterfaceProxy


class IFocusModelProxy(InterfaceProxy):
    def get_optimal_focus(self) -> 'Future[float]':
        ...

    def set_optimal_focus(self) -> 'Future[None]':
        ...

