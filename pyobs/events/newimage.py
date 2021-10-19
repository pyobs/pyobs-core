from typing import Optional

from .event import Event
from ..utils.enums import ImageType


class NewImageEvent(Event):
    """Event to be sent on a new image."""
    __module__ = 'pyobs.events'

    def __init__(self, filename: Optional[str] = None, image_type: Optional[ImageType] = None,
                 raw: Optional[str] = None):
        """Initializes new NewImageEvent.

        Args:
            filename: Name of new image file.
            image_type: Type of image.
            raw: Only for reduced images, references raw frame.
        """
        Event.__init__(self)
        self.data = {
            'filename': filename,
            'image_type': 'object' if image_type is None else image_type.value,
            'raw': raw
        }

    @property
    def filename(self) -> Optional[str]:
        return str(self.data['filename']) if 'filename' in self.data else None

    @property
    def image_type(self) -> Optional[ImageType]:
        return ImageType(self.data['image_type']) if 'image_type' in self.data else None

    @property
    def raw(self) -> Optional[str]:
        return str(self.data['raw']) if 'raw' in self.data else None

    @property
    def is_reduced(self) -> bool:
        return self.raw is not None


__all__ = ['NewImageEvent']
