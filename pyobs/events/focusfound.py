from typing import Optional
from typing_extensions import TypedDict

from .event import Event


DataType = TypedDict('DataType', {'focus': Optional[float], 'error': Optional[float], 'filter_name': Optional[str]})


class FocusFoundEvent(Event):
    """Event to be sent when a new best focus has been found, e.g. after a focus series."""
    __module__ = 'pyobs.events'

    def __init__(self, focus: Optional[float] = None, error: Optional[float] = None, filter_name: Optional[str] = None):
        Event.__init__(self)
        self.data: DataType = {'focus': focus, 'error': error, 'filter_name': filter_name}

    @property
    def focus(self) -> Optional[float]:
        return self.data['focus']

    @property
    def error(self) -> Optional[float]:
        return self.data['error']

    @property
    def filter_name(self) -> Optional[str]:
        return self.data['filter_name']


__all__ = ['FocusFoundEvent']
