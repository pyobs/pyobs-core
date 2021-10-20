from typing import Any

from .interface import Interface
from pyobs.utils.enums import ImageType


class IImageType(Interface):
    """The module supports different image types (e.g. object, bias, dark, etc), mainly used by cameras."""
    __module__ = 'pyobs.interfaces'

    def set_image_type(self, image_type: ImageType, **kwargs: Any) -> None:
        """Set the image type.

        Args:
            image_type: New image type.
        """
        raise NotImplementedError

    def get_image_type(self, **kwargs: Any) -> ImageType:
        """Returns the current image type.

        Returns:
            Current image type.
        """
        raise NotImplementedError


__all__ = ['IImageType']
