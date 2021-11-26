from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from pyobs.utils.threads import Future
from .IAbortableProxy import IAbortableProxy
from .interfaceproxy import InterfaceProxy


class IAutoFocusProxy(IAbortableProxy, InterfaceProxy):
    def abort(self) -> 'Future[None]':
        ...

    def auto_focus(self, count: int, step: float, exposure_time: float) -> 'Future[typing.Tuple[float, float]]':
        ...

    def auto_focus_status(self) -> 'Future[typing.Dict[str, typing.Any]]':
        ...

