from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from pyobs.utils.threads import Future
from .interfaceproxy import InterfaceProxy


class IReadyProxy(InterfaceProxy):
    def is_ready(self) -> 'Future[bool]':
        ...

