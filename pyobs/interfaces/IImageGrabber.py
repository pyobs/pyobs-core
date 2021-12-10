from typing import Any

from .interface import Interface


class IImageGrabber(Interface):
    """The module can grab and return an image from whatever device."""
    __module__ = 'pyobs.interfaces'

    async def grab_image(self, broadcast: bool = True, **kwargs: Any) -> str:
        """Grabs an image and returns reference.

        Args:
            broadcast: Broadcast existence of image.

        Returns:
            Name of image that was taken.
        """
        raise NotImplementedError


__all__ = ['IImageGrabber']
