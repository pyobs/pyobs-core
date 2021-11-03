from typing import Optional, Any, Dict
from typing_extensions import TypedDict

from pyobs.utils.time import Time
from pyobs.events.event import Event


DataType = TypedDict('DataType', {'name': str, 'id': Any, 'eta': Optional[str]})


class TaskStartedEvent(Event):
    """Event to be sent when a task has started."""
    __module__ = 'pyobs.events'

    def __init__(self, name: str, id: Any, eta: Optional[Time] = None, **kwargs: Any):
        """Initializes a new task started event.

        Args:
            name: Name of task that just started
            id: Unique identifier for task
            eta: Predicted ETA for when the task will finish
        """
        Event.__init__(self)
        self.data: DataType = {
            'name': name,
            'id': id,
            'eta':  None if eta is None else eta.isot
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> Event:
        # get name
        if 'name' not in d or not isinstance(d['name'], str):
            raise ValueError('Invalid type for name.')
        name: str = d['name']

        # get id
        if 'id' not in d:
            raise ValueError('Invalid type for id.')
        id: Any = d['id']

        # get eta
        eta: Optional[Time] = None
        if 'eta' in d and isinstance(d['eta'], str):
            eta = Time(d['eta'])

        # return object
        return TaskStartedEvent(name=name, id=id, eta=eta)

    @property
    def name(self) -> str:
        return self.data['name']

    @property
    def id(self) -> Any:
        return self.data['id']

    @property
    def eta(self) -> Optional[Time]:
        return Time(self.data['eta']) if self.data['eta'] is not None else None


__all__ = ['TaskStartedEvent']
