from typing import Optional, Any

from pyobs.utils.time import Time
from .event import Event


class TaskStartedEvent(Event):
    """Event to be sent when a task has started."""
    __module__ = 'pyobs.events'

    def __init__(self, name: Optional[str] = None, id: Optional[Any] = None, eta: Optional[Time] = None):
        """Initializes a new task started event.

        Args:
            name: Name of task that just started
            id: Unique identifier for task
            eta: Predicted ETA for when the task will finish
        """
        Event.__init__(self)
        self.data = {
            'name': name,
            'id': id,
            'eta':  None if eta is None else eta.isot
        }

    @property
    def name(self) -> Optional[str]:
        return str(self.data['name']) if self.data['name'] is not None else None

    @property
    def id(self) -> Optional[Any]:
        return self.data['id']

    @property
    def eta(self) -> Optional[Time]:
        return Time(self.data['eta']) if self.data['eta'] is not None else None


__all__ = ['TaskStartedEvent']
