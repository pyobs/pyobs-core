from .event import Event


class FocusFoundEvent(Event):
    """Event to be sent when a new best focus has been found, e.g. after a focus series."""

    def __init__(self, focus: float = None):
        Event.__init__(self)
        self.data = focus

    @property
    def focus(self):
        return self.data


__all__ = ['FocusFoundEvent']
