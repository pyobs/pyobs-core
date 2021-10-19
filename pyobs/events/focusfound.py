from typing import Optional

from .event import Event


class FocusFoundEvent(Event):
    """Event to be sent when a new best focus has been found, e.g. after a focus series."""
    __module__ = 'pyobs.events'

    def __init__(self, focus: Optional[float] = None, error: Optional[float] = None, filter_name: Optional[str] = None):
        Event.__init__(self)
        self.data = {'focus': focus, 'error': error, 'filter': filter_name}

    @property
    def focus(self) -> Optional[float]:
        return self.data['focus'] if 'focus' in self.data else None

    @property
    def error(self) -> Optional[float]:
        return self.data['error'] if 'error' in self.data else None

    @property
    def filter_name(self) -> Optional[str]:
        return self.data['filter'] if 'filter' in self.data else None


__all__ = ['FocusFoundEvent']
