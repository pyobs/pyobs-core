from abc import ABCMeta, abstractmethod
from typing import Any

from .interface import Interface


class IImageGrabber(Interface, metaclass=ABCMeta):
    """The module can grab and return an image from whatever device."""

    __module__ = "pyobs.interfaces"

    @abstractmethod
    async def grab_image(self, broadcast: bool = True, **kwargs: Any) -> str:
        """Grabs an image and returns reference.

        Args:
            broadcast: Broadcast existence of image.

        Returns:
            Name of image that was taken.

        Raises:
            GrabImageError: If there was a problem grabbing the image.
        """
        ...


__all__ = ["IImageGrabber"]
