from pyobs.utils.time import Time

from .event import Event


class GoodWeatherEvent(Event):
    __module__ = 'pyobs.events'

    def __init__(self, eta: Time = None):
        """Initializes a new good weather event.

        Args:
            eta: Predicted ETA for when the telescope will be fully operational
        """
        Event.__init__(self)
        self.data = None if eta is None else eta.isot

    @property
    def eta(self):
        return None if self.data is None else Time(self.data)


__all__ = ['GoodWeatherEvent']
