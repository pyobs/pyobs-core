from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from pyobs.utils.threads import Future
from .interfaceproxy import InterfaceProxy


class IWindowProxy(InterfaceProxy):
    __module__ = 'pyobs.interfaces.proxies'

    def get_full_frame(self) -> 'Future[typing.Tuple[int, int, int, int]]':
        ...

    def get_window(self) -> 'Future[typing.Tuple[int, int, int, int]]':
        ...

    def set_window(self, left: int, top: int, width: int, height: int) -> 'Future[None]':
        ...

