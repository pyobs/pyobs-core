from typing import Optional, Any
from typing_extensions import TypedDict

from .event import Event


DataType = TypedDict('DataType', {'name': Optional[str], 'id': Optional[Any]})


class TaskFinishedEvent(Event):
    """Event to be sent when a task has finished."""
    __module__ = 'pyobs.events'

    def __init__(self, name: Optional[str] = None, id: Optional[Any] = None, **kwargs: Any):
        """Initializes a new task finished event.

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
    def name(self) -> Optional[str]:
        return self.data['name']

    @property
    def id(self) -> Optional[Any]:
        return self.data['id']


__all__ = ['TaskFinishedEvent']
