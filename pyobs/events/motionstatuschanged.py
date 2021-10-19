from typing import Optional, Dict
from typing_extensions import TypedDict

from .event import Event
from ..utils.enums import MotionStatus


DataType = TypedDict('DataType', {'status': Optional[str], 'interfaces': Dict[str, str]})


class MotionStatusChangedEvent(Event):
    """Event to be sent when the motion status of a device has changed."""
    __module__ = 'pyobs.events'

    def __init__(self, status: Optional[MotionStatus] = None, interfaces: Optional[Dict[str, MotionStatus]] = None):
        Event.__init__(self)
        self.data: DataType = {
            'status': status.value if status is not None else None,
            'interfaces': {k: v.value for k, v in interfaces.items()} if interfaces is not None else {}
        }

    @property
    def status(self) -> Optional[MotionStatus]:
        return MotionStatus(self.data['status']) if self.data['status'] is not None else None

    @property
    def interfaces(self) -> Dict[str, MotionStatus]:
        return {k: MotionStatus(v) for k, v in self.data['interfaces'].items()}


__all__ = ['MotionStatusChangedEvent']
