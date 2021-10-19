from typing import Optional, Any

from .event import Event


class TaskFinishedEvent(Event):
    """Event to be sent when a task has finished."""
    __module__ = 'pyobs.events'

    def __init__(self, name: Optional[str] = None, id: Optional[Any] = None):
        """Initializes a new task finished event.

        Args:
            name: Name of task that just finished
            id: Unique identifier for task
        """
        Event.__init__(self)
        self.data = {
            'name': name,
            'id': id
        }

    @property
    def name(self) -> Optional[str]:
        return self.data['name'] if 'name' in self.data else None

    @property
    def id(self) -> Optional[Any]:
        return self.data['id'] if 'id' in self.data else None


__all__ = ['TaskFinishedEvent']
