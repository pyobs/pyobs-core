from typing import Optional
from typing_extensions import TypedDict

from .event import Event


DataType = TypedDict('DataType', {'filter': Optional[str]})


class FilterChangedEvent(Event):
    """Event to be sent when a filter has been changed."""
    __module__ = 'pyobs.events'

    def __init__(self, current: Optional[str] = None):
        Event.__init__(self)
        self.data: DataType = {'filter': current}

    @property
    def filter(self) -> Optional[str]:
        return self.data['filter']


__all__ = ['FilterChangedEvent']
