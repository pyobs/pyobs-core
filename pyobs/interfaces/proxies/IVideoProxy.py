from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from pyobs.utils.threads import Future
from .IImageGrabberProxy import IImageGrabberProxy
from .interfaceproxy import InterfaceProxy


class IVideoProxy(IImageGrabberProxy, InterfaceProxy):
    def get_video(self) -> 'Future[str]':
        ...

    def grab_image(self, broadcast: bool = True) -> 'Future[str]':
        ...

