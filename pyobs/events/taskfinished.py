import typing

from .event import Event


class TaskFinishedEvent(Event):
    def __init__(self, name: str = None, id: typing.Any = None,):
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
    def name(self):
        return self.data['name']

    @property
    def id(self):
        return self.data['id']


__all__ = ['TaskFinishedEvent']
