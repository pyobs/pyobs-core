from typing import Optional, Any
from typing_extensions import TypedDict

from pyobs.events.event import Event


DataType = TypedDict('DataType', {'time': str, 'level': str, 'filename': str,
                                  'function': str, 'line': int, 'message': str})


class LogEvent(Event):
    """Event for log entries."""
    __module__ = 'pyobs.events'

    def __init__(self, time: str, level: str, filename: str, function: str, line: int, message: str,
                 **kwargs: Any):
        Event.__init__(self)
        self.data: DataType = {
            'time': time,
            'level': level,
            'filename': filename,
            'function': function,
            'line': line,
            'message': message
        }

    @property
    def time(self) -> str:
        return str(self.data['time'])

    @property
    def level(self) -> str:
        return str(self.data['level'])

    @property
    def filename(self) -> str:
        return str(self.data['filename'])

    @property
    def function(self) -> str:
        return str(self.data['function'])

    @property
    def line(self) -> Optional[int]:
        return int(self.data['line'])

    @property
    def message(self) -> str:
        return str(self.data['message'])


__all__ = ['LogEvent']
