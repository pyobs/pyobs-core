from typing import Optional, Any, Dict
from typing_extensions import TypedDict

from pyobs.utils.time import Time
from pyobs.events.event import Event


DataType = TypedDict('DataType', {'eta': Optional[str]})


class GoodWeatherEvent(Event):
    """Event to be sent on good weather."""
    __module__ = 'pyobs.events'

    def __init__(self, eta: Optional[Time] = None, **kwargs: Any):
        """Initializes a new good weather event.

        Args:
            eta: Predicted ETA for when the telescope will be fully operational
        """
        Event.__init__(self)
        self.data: DataType = {'eta': eta.isot if eta is not None else None}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> Event:
        # get eta
        eta: Optional[Time] = None
        if 'eta' in d and isinstance(d['eta'], str):
            eta = Time(d['eta'])

        # return object
        return GoodWeatherEvent(eta=eta)

    @property
    def eta(self) -> Optional[Time]:
        return Time(self.data['eta']) if self.data['eta'] is not None else None


__all__ = ['GoodWeatherEvent']
