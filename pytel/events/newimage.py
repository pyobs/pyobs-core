from .event import Event


class NewImageEvent(Event):
    def __init__(self, filename=None):
        Event.__init__(self)
        self.data = {
            'filename': filename
        }

    @property
    def filename(self):
        return self.data['filename']


__all__ = ['NewImageEvent']
