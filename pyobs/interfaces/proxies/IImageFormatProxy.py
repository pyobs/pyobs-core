from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from pyobs.utils.threads import Future
from pyobs.utils.enums import ImageFormat
from .interfaceproxy import InterfaceProxy


class IImageFormatProxy(InterfaceProxy):
    def get_image_format(self) -> 'Future[ImageFormat]':
        ...

    def list_image_formats(self) -> 'Future[typing.List[str]]':
        ...

    def set_image_format(self, format: ImageFormat) -> 'Future[None]':
        ...

