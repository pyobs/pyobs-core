from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from pyobs.utils.enums import ImageFormat

from ..utils.time import Time
from .interface import Interface


@dataclass
class ImageFormatState:
    image_format: ImageFormat
    time: Time = field(default_factory=Time.now)


@dataclass
class ImageFormatCapabilities:
    image_formats: list[str] = field(default_factory=list)


class IImageFormat(Interface, metaclass=ABCMeta):
    """The module supports different image formats (e.g. INT16, FLOAT32), mainly used by cameras."""

    __module__ = "pyobs.interfaces"

    state = ImageFormatState
    capabilities = ImageFormatCapabilities

    @abstractmethod
    async def set_image_format(self, fmt: ImageFormat, **kwargs: Any) -> None:
        """Set the camera image format.

        Args:
            fmt: New image format.

        Raises:
            ValueError: If format could not be set.
        """
        ...


__all__ = ["IImageFormat", "ImageFormatState", "ImageFormatCapabilities"]
