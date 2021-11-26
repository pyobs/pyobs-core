from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from pyobs.utils.threads import Future
from .interfaceproxy import InterfaceProxy


class IImageGrabberProxy(InterfaceProxy):
    def grab_image(self, broadcast: bool = True) -> 'Future[str]':
        ...

