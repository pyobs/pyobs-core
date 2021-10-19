from typing import Optional

from pyobs.utils.time import Time
from .event import Event


class GoodWeatherEvent(Event):
    """Event to be sent on good weather."""
    __module__ = 'pyobs.events'

    def __init__(self, eta: Optional[Time] = None):
        """Initializes a new good weather event.

        Args:
            eta: Predicted ETA for when the telescope will be fully operational
        """
        Event.__init__(self)
        if eta is not None:
            self.data = {'eta': eta.isot}

    @property
    def eta(self) -> Optional[Time]:
        return Time(self.data['eta']) if 'eta' in self.data else None


__all__ = ['GoodWeatherEvent']
