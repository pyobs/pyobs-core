import typing

from pyobs.interfaces import IMotion
from .event import Event


class MotionStatusChangedEvent(Event):
    def __init__(self, status: IMotion.Status = None, interfaces: typing.Dict[str, IMotion.Status] = None):
        Event.__init__(self)
        self.data = {}
        if status is not None:
            self.data['status'] = status.value
        if interfaces is not None:
            self.data['interfaces'] = {k: v.value for k, v in interfaces.items()}

    @property
    def status(self):
        if self.data is None or 'status' not in self.data:
            return None
        return IMotion.Status(self.data['status'])

    @property
    def interfaces(self):
        if self.data is None or 'interfaces' not in self.data:
            return {}
        return {k: IMotion.Status(v) for k, v in self.data['interfaces'].items()}


__all__ = ['MotionStatusChangedEvent']
