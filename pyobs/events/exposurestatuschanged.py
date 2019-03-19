from pyobs.interfaces import ICamera
from .event import Event


class ExposureStatusChangedEvent(Event):
    def __init__(self, last: ICamera.ExposureStatus = None, current: ICamera.ExposureStatus = None):
        Event.__init__(self)
        self.data = None
        if last is not None and current is not None:
            self.data = {'last': last.name, 'current': current.name}

    @property
    def last(self):
        return None if self.data is None else ICamera.ExposureStatus[self.data['last']]

    @property
    def current(self):
        return None if self.data is None else ICamera.ExposureStatus[self.data['current']]


__all__ = ['ExposureStatusChangedEvent']
