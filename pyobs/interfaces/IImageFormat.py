from typing import List, Any

from .interface import Interface
from pyobs.utils.enums import ImageFormat


class IImageFormat(Interface):
    """The module supports different image formats (e.g. INT16, FLOAT32), mainly used by cameras."""
    __module__ = 'pyobs.interfaces'

    async def set_image_format(self, format: ImageFormat, **kwargs: Any) -> None:
        """Set the camera image format.

        Args:
            format: New image format.

        Raises:
            ValueError: If format could not be set.
        """
        raise NotImplementedError

    async def get_image_format(self, **kwargs: Any) -> ImageFormat:
        """Returns the camera image format.

        Returns:
            Current image format.
        """
        raise NotImplementedError

    async def list_image_formats(self, **kwargs: Any) -> List[str]:
        """List available image formats.

        Returns:
            List of available image formats.
        """
        raise NotImplementedError


__all__ = ['IImageFormat']
