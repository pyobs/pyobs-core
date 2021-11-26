from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from pyobs.utils.threads import Future
from .interfaceproxy import InterfaceProxy


class ISyncTargetProxy(InterfaceProxy):
    def sync_target(self) -> 'Future[None]':
        ...

