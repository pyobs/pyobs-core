from typing import Optional, Any
from typing_extensions import TypedDict

from pyobs.events.event import Event


DataType = TypedDict('DataType', {'name': str, 'id': Any})


class TaskFailedEvent(Event):
    """Event to be sent when a task has failed."""
    __module__ = 'pyobs.events'

    def __init__(self, name: str, id: Any, **kwargs: Any):
        """Initializes a new task failed event.

        Args:
            name: Name of task that just finished
            id: Unique identifier for task
        """
        Event.__init__(self)
        self.data: DataType = {
            'name': name,
            'id': id
        }

    @property
    def name(self) -> str:
        return self.data['name']

    @property
    def id(self) -> Any:
        return self.data['id']


__all__ = ['TaskFailedEvent']
