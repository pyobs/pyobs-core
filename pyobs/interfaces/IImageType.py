from .interface import *
from pyobs.utils.enums import ImageType


class IImageType(Interface):
    __module__ = 'pyobs.interfaces'

    def set_image_type(self, image_type: ImageType, *args, **kwargs):
        """Set the image type.

        Args:
            image_type: New image type.
        """
        raise NotImplementedError

    def get_image_type(self, *args, **kwargs) -> ImageType:
        """Returns the current image type.

        Returns:
            Current image type.
        """
        raise NotImplementedError


__all__ = ['IImageType']
