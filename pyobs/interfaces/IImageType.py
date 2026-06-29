from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from pyobs.utils.enums import ImageType

from ..utils.time import Time
from .interface import Interface


@dataclass
class ImageTypeState:
    image_type: ImageType
    time: Time = field(default_factory=Time.now)


class IImageType(Interface, metaclass=ABCMeta):
    """The module supports different image types (e.g. object, bias, dark, etc), mainly used by cameras."""

    __module__ = "pyobs.interfaces"

    state = ImageTypeState

    @abstractmethod
    async def set_image_type(self, image_type: ImageType, **kwargs: Any) -> None:
        """Set the image type.

        Args:
            image_type: New image type.
        """
        ...


__all__ = ["IImageType", "ImageTypeState"]
