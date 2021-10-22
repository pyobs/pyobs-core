from typing import Optional
from typing_extensions import TypedDict

from .event import Event
from ..utils.enums import ImageType


DataType = TypedDict('DataType', {'filename': Optional[str], 'image_type': Optional[str], 'raw': Optional[str]})


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
        self.data: DataType = {
            'filename': filename,
            'image_type': image_type.value if image_type is not None else None,
            'raw': raw
        }

    @property
    def filename(self) -> Optional[str]:
        return self.data['filename']

    @property
    def image_type(self) -> Optional[ImageType]:
        return ImageType(self.data['image_type']) if 'image_type' in self.data else None

    @property
    def raw(self) -> Optional[str]:
        return self.data['raw']

    @property
    def is_reduced(self) -> bool:
        return self.raw is not None


__all__ = ['NewImageEvent']
