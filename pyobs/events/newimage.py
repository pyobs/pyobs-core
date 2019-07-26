from .event import Event

from pyobs.interfaces import ICamera


class NewImageEvent(Event):
    def __init__(self, filename: str = None, image_type: ICamera.ImageType = None):
        Event.__init__(self)
        self.data = {
            'filename': filename,
            'image_type': image_type.value
        }

    @property
    def filename(self):
        return self.data['filename']

    @property
    def image_type(self):
        return ICamera.ImageType(self.data['image_type'])


__all__ = ['NewImageEvent']
