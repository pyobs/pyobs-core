from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from pyobs.utils.enums import ImageType

from ..utils.time import Time
from .interface import Interface


class IImageType(Interface, metaclass=ABCMeta):
    """The module supports different image types (e.g. object, bias, dark, etc), mainly used by cameras."""

    __module__ = "pyobs.interfaces"

    @dataclass
    class State:
        image_type: ImageType
        time: Time = field(default_factory=Time.now)

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
