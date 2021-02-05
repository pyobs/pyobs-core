from .interface import Interface
from ..utils.enums import ImageFormat


class IImageFormat(Interface):
    """For cameras supporting different image formats, e.g. INT16 or RGB24"""

    def set_image_format(self, format: ImageFormat, *args, **kwargs):
        """Set the camera image format.

        Args:
            format: New image format.

        Raises:
            ValueError: If format could not be set.
        """
        raise NotImplementedError

    def get_image_format(self, *args, **kwargs) -> ImageFormat:
        """Returns the camera image format.

        Returns:
            Current image format.
        """
        raise NotImplementedError

    def list_image_formats(self, *args, **kwargs) -> list:
        """List available image formats.

        Returns:
            List of available image formats.
        """
        raise NotImplementedError


__all__ = ['IImageFormat']
