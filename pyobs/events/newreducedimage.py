from .event import Event


class NewReducedImageEvent(Event):
    def __init__(self, filename: str = None, raw: str = None):
        Event.__init__(self)
        self.data = {
            'filename': filename,
            'raw': raw
        }

    @property
    def filename(self):
        return self.data['filename']

    @property
    def raw(self):
        return self.data['raw']


__all__ = ['NewReducedImageEvent']
