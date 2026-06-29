from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from pyobs.utils.enums import ImageFormat

from ..utils.time import Time
from .interface import Interface


class IImageFormat(Interface, metaclass=ABCMeta):
    """The module supports different image formats (e.g. INT16, FLOAT32), mainly used by cameras."""

    __module__ = "pyobs.interfaces"

    @dataclass
    class State:
        image_format: ImageFormat
        time: Time = field(default_factory=Time.now)

    @dataclass
    class Capabilities:
        image_formats: list[str] = field(default_factory=list)

    @abstractmethod
    async def set_image_format(self, fmt: ImageFormat, **kwargs: Any) -> None:
        """Set the camera image format.

        Args:
            fmt: New image format.

        Raises:
            ValueError: If format could not be set.
        """
        ...


__all__ = ["IImageFormat"]
