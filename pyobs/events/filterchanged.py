from typing import Optional, Any
from typing_extensions import TypedDict

from .event import Event


DataType = TypedDict('DataType', {'current': Optional[str]})


class FilterChangedEvent(Event):
    """Event to be sent when a filter has been changed."""
    __module__ = 'pyobs.events'

    def __init__(self, current: Optional[str] = None, **kwargs: Any):
        Event.__init__(self)
        self.data: DataType = {'current': current}

    @property
    def filter(self) -> Optional[str]:
        return self.data['current']


__all__ = ['FilterChangedEvent']
