from typing import Optional
from typing_extensions import TypedDict

from .event import Event
from pyobs.utils.enums import ExposureStatus


DataType = TypedDict('DataType', {'last': Optional[str], 'current': Optional[str]})


class ExposureStatusChangedEvent(Event):
    """Event to be sent, when the exposure status of a device changes."""
    __module__ = 'pyobs.events'

    def __init__(self, last: Optional[ExposureStatus] = None, current: Optional[ExposureStatus] = None):
        Event.__init__(self)
        self.data: DataType = {'last': last.value if last is not None else None,
                               'current': current.value if current is not None else None}

    @property
    def last(self) -> Optional[ExposureStatus]:
        return ExposureStatus(self.data['last']) if self.data['last'] is not None else None

    @property
    def current(self) -> Optional[ExposureStatus]:
        return ExposureStatus(self.data['current']) if self.data['current'] is not None else None


__all__ = ['ExposureStatusChangedEvent']
