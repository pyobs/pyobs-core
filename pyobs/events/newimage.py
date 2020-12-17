from .event import Event
from ..utils.enums import ImageType


class NewImageEvent(Event):
    def __init__(self, filename: str = None, image_type: ImageType = None, raw: str = None):
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
    def filename(self):
        return self.data['filename']

    @property
    def image_type(self):
        return ImageType(self.data['image_type'])

    @property
    def raw(self):
        return self.data['raw']

    @property
    def is_reduced(self):
        return self.raw is not None


__all__ = ['NewImageEvent']
