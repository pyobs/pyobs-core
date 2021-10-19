from typing import Optional, Dict, List

from .event import Event
from ..utils.enums import MotionStatus


class MotionStatusChangedEvent(Event):
    """Event to be sent when the motion status of a device has changed."""
    __module__ = 'pyobs.events'

    def __init__(self, status: Optional[MotionStatus] = None,
                 interfaces: Optional[Dict[str, MotionStatus]] = None):
        Event.__init__(self)
        self.data = {}
        if status is not None:
            self.data['status'] = status.value
        if interfaces is not None:
            self.data['interfaces'] = {k: v.value for k, v in interfaces.items()}

    @property
    def status(self) -> Optional[MotionStatus]:
        if self.data is None or 'status' not in self.data:
            return None
        return MotionStatus(self.data['status'])

    @property
    def interfaces(self) -> Dict[str, MotionStatus]:
        if self.data is None or 'interfaces' not in self.data:
            return {}
        return {k: MotionStatus(v) for k, v in self.data['interfaces'].items()}


__all__ = ['MotionStatusChangedEvent']
