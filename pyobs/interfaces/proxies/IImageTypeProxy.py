import typing

from pyobs.utils.threads import Future
from pyobs.utils.enums import ImageType
from .interfaceproxy import InterfaceProxy


class IImageTypeProxy(InterfaceProxy):
    def get_image_type(self) -> Future[ImageType]:
        ...

    def set_image_type(self, image_type: ImageType) -> Future[None]:
        ...

