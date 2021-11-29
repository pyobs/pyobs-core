from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from pyobs.utils.threads import Future
from .IImageGrabberProxy import IImageGrabberProxy
from .interfaceproxy import InterfaceProxy


class IVideoProxy(IImageGrabberProxy, InterfaceProxy):
    __module__ = 'pyobs.interfaces.proxies'

    def get_video(self) -> 'Future[str]':
        ...

    def grab_image(self, broadcast: bool = True) -> 'Future[str]':
        ...

