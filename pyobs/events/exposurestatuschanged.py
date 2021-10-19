from typing import Optional

from .event import Event
from pyobs.utils.enums import ExposureStatus


class ExposureStatusChangedEvent(Event):
    """Event to be sent, when the exposure status of a device changes."""
    __module__ = 'pyobs.events'

    def __init__(self, last: Optional[ExposureStatus] = None, current: Optional[ExposureStatus] = None):
        Event.__init__(self)
        if last is not None and current is not None:
            self.data = {'last': last.value, 'current': current.value}

    @property
    def last(self) -> Optional[ExposureStatus]:
        return ExposureStatus(self.data['last']) if self.data['last'] is not None else None

    @property
    def current(self) -> Optional[ExposureStatus]:
        return ExposureStatus(self.data['current']) if self.data['current'] is not None else None


__all__ = ['ExposureStatusChangedEvent']
