from typing import Optional
from typing_extensions import TypedDict

from .event import Event


DataType = TypedDict('DataType', {'time': Optional[str], 'level': Optional[str], 'filename': Optional[str],
                                  'function': Optional[str], 'line': Optional[int], 'message': Optional[str]})


class LogEvent(Event):
    """Event for log entries."""
    __module__ = 'pyobs.events'

    def __init__(self, time: Optional[str] = None, level: Optional[str] = None, filename: Optional[str] = None,
                 function: Optional[str] = None, line: Optional[int] = None, message: Optional[str] = None):
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
    def time(self) -> Optional[str]:
        return str(self.data['time']) if self.data['time'] is not None else None

    @property
    def level(self) -> Optional[str]:
        return str(self.data['level']) if self.data['level'] is not None else None

    @property
    def filename(self) -> Optional[str]:
        return str(self.data['filename']) if self.data['filename'] is not None else None

    @property
    def function(self) -> Optional[str]:
        return str(self.data['function']) if self.data['function'] is not None else None

    @property
    def line(self) -> Optional[int]:
        return int(self.data['line']) if self.data['line'] is not None else None

    @property
    def message(self) -> Optional[str]:
        return str(self.data['message']) if self.data['message'] is not None else None


__all__ = ['LogEvent']
