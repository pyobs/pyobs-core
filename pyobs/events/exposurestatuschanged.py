from typing import Optional

from .event import Event
from pyobs.utils.enums import ExposureStatus


class ExposureStatusChangedEvent(Event):
    """Event to be sent, when the exposure status of a device changes."""
    __module__ = 'pyobs.events'

    def __init__(self, last: Optional[ExposureStatus] = None, current: Optional[ExposureStatus] = None):
        Event.__init__(self)
        self.data = None
        if last is not None and current is not None:
            self.data = {'last': last.value, 'current': current.value}

    @property
    def last(self) -> Optional[ExposureStatus]:
        return None if self.data is None else ExposureStatus(self.data['last'])

    @property
    def current(self) -> Optional[ExposureStatus]:
        return None if self.data is None else ExposureStatus(self.data['current'])


__all__ = ['ExposureStatusChangedEvent']
