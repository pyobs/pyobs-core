import typing

from pyobs.utils.threads import Future
from .InterfaceProxy import InterfaceProxy


class IReadyProxy(InterfaceProxy):
    def is_ready(self) -> Future[bool]:
        ...

