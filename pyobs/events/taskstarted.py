import typing

from pyobs.utils.time import Time
from .event import Event


class TaskStartedEvent(Event):
    def __init__(self, name: str = None, id: typing.Any = None, eta: Time = None):
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
    def name(self):
        return self.data['name']

    @property
    def id(self):
        return self.data['id']

    @property
    def eta(self):
        return None if self.data is None else Time(self.data['eta'])


__all__ = ['TaskStartedEvent']
