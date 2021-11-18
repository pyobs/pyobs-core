from __future__ import annotations
from typing import Dict, Any
from typing_extensions import TypedDict

from pyobs.events.event import Event


DataType = TypedDict('DataType', {'filename': str})


class NewSpectrumEvent(Event):
    """Event to be sent on a new image."""
    __module__ = 'pyobs.events'

    def __init__(self, filename: str, **kwargs: Any):
        """Initializes new NewSpectrumEvent.

        Args:
            filename: Name of new image file.
        """
        Event.__init__(self)
        self.data: DataType = {
            'filename': filename
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> Event:
        # get filename
        if 'filename' not in d or not isinstance(d['filename'], str):
            raise ValueError('Invalid type for filename.')
        filename: str = d['filename']

        # return object
        return NewSpectrumEvent(filename)

    @property
    def filename(self) -> str:
        return self.data['filename']


__all__ = ['NewSpectrumEvent']
