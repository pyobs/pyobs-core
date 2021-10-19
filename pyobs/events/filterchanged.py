from typing import Optional

from .event import Event


class FilterChangedEvent(Event):
    """Event to be sent when a filter has been changed."""
    __module__ = 'pyobs.events'

    def __init__(self, current: Optional[str] = None):
        Event.__init__(self)
        self.data = {'filter': current}

    @property
    def filter(self) -> Optional[str]:
        return self.data['filter']


__all__ = ['FilterChangedEvent']
