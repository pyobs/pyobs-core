from pyobs.interfaces import IMotion
from .event import Event


class MotionStatusChangedEvent(Event):
    def __init__(self, last: IMotion.Status = None, current: IMotion.Status = None):
        Event.__init__(self)
        self.data = None
        if last is not None and current is not None:
            self.data = {'last': last.value, 'current': current.value}

    @property
    def last(self):
        return None if self.data is None else IMotion.Status(self.data['last'])

    @property
    def current(self):
        return None if self.data is None else IMotion.Status(self.data['current'])


__all__ = ['MotionStatusChangedEvent']
