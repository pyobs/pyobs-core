import typing

from pyobs.utils.threads import Future
from .InterfaceProxy import InterfaceProxy


class ISyncTargetProxy(InterfaceProxy):
    def sync_target(self) -> Future[None]:
        ...

