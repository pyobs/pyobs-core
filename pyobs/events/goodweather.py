from typing import Optional
from typing_extensions import TypedDict

from pyobs.utils.time import Time
from .event import Event


DataType = TypedDict('DataType', {'eta': Optional[str]})


class GoodWeatherEvent(Event):
    """Event to be sent on good weather."""
    __module__ = 'pyobs.events'

    def __init__(self, eta: Optional[Time] = None):
        """Initializes a new good weather event.

        Args:
            eta: Predicted ETA for when the telescope will be fully operational
        """
        Event.__init__(self)
        self.data: DataType = {'eta': eta.isot if eta is not None else None}

    @property
    def eta(self) -> Optional[Time]:
        return Time(self.data['eta']) if self.data['eta'] is not None else None


__all__ = ['GoodWeatherEvent']
