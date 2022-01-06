from abc import ABCMeta, abstractmethod
from typing import Any

from .interface import Interface
from pyobs.utils.enums import ImageType


class IImageType(Interface, metaclass=ABCMeta):
    """The module supports different image types (e.g. object, bias, dark, etc), mainly used by cameras."""

    __module__ = "pyobs.interfaces"

    @abstractmethod
    async def set_image_type(self, image_type: ImageType, **kwargs: Any) -> None:
        """Set the image type.

        Args:
            image_type: New image type.
        """
        ...

    @abstractmethod
    async def get_image_type(self, **kwargs: Any) -> ImageType:
        """Returns the current image type.

        Returns:
            Current image type.
        """
        ...


__all__ = ["IImageType"]
