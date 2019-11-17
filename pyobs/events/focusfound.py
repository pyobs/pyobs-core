from .event import Event


class FocusFoundEvent(Event):
    """Event to be sent when a new best focus has been found, e.g. after a focus series."""

    def __init__(self, focus: float = None, error: float = None, filter_name: str = None):
        Event.__init__(self)
        self.data = {'focus': focus, 'error': error, 'filter': filter_name}

    @property
    def focus(self):
        return self.data['focus']

    @property
    def error(self):
        return self.data['error']

    @property
    def filter_name(self):
        return self.data['filter']


__all__ = ['FocusFoundEvent']
