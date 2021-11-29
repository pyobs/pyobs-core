from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from pyobs.utils.threads import Future
from pyobs.utils.enums import ImageType
from .interfaceproxy import InterfaceProxy


class IImageTypeProxy(InterfaceProxy):
    __module__ = 'pyobs.interfaces.proxies'

    def get_image_type(self) -> 'Future[ImageType]':
        ...

    def set_image_type(self, image_type: ImageType) -> 'Future[None]':
        ...

