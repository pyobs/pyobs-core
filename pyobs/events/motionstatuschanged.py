from typing import Optional, Dict, Any
from typing_extensions import TypedDict

from pyobs.events.event import Event
from pyobs.utils.enums import MotionStatus


DataType = TypedDict('DataType', {'status': str, 'interfaces': Dict[str, str]})


class MotionStatusChangedEvent(Event):
    """Event to be sent when the motion status of a device has changed."""
    __module__ = 'pyobs.events'

    def __init__(self, status: MotionStatus, interfaces: Optional[Dict[str, MotionStatus]] = None,
                 **kwargs: Any):
        Event.__init__(self)
        self.data: DataType = {
            'status': status.value,
            'interfaces': {k: v.value for k, v in interfaces.items()} if interfaces is not None else {}
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> Event:
        # get status
        if 'status' not in d or not isinstance(d['status'], str):
            raise ValueError('Invalid type for status.')
        status: MotionStatus = MotionStatus(d['status'])

        # get interfaces
        interfaces: Optional[Dict[str, MotionStatus]] = {}
        if 'interfaces' in d and isinstance(d['interfaces'], dict):
            interfaces = {k: MotionStatus(v) for k, v in d['interfaces'].items()}

        # return object
        return MotionStatusChangedEvent(status, interfaces)

    @property
    def status(self) -> Optional[MotionStatus]:
        return MotionStatus(self.data['status']) if self.data['status'] is not None else None

    @property
    def interfaces(self) -> Dict[str, MotionStatus]:
        return {k: MotionStatus(v) for k, v in self.data['interfaces'].items()}


__all__ = ['MotionStatusChangedEvent']
