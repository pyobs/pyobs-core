from typing import Optional

from .event import Event


class LogEvent(Event):
    """Event for log entries."""
    __module__ = 'pyobs.events'

    def __init__(self, time: Optional[str] = None, level: Optional[str] = None, filename: Optional[str] = None,
                 function: Optional[str] = None, line: Optional[int] = None, message: Optional[str] = None):
        Event.__init__(self)
        self.data = {
            'time': time,
            'level': level,
            'filename': filename,
            'function': function,
            'line': line,
            'message': message
        }

    @property
    def time(self) -> Optional[str]:
        return str(self.data['time']) if 'time' in self.data and self.data['time'] is not None else None

    @property
    def level(self) -> Optional[str]:
        return str(self.data['level']) if 'level' in self.data and self.data['level'] is not None else None

    @property
    def filename(self) -> Optional[str]:
        return str(self.data['filename']) if 'filename' in self.data and self.data['filename'] is not None else None

    @property
    def function(self) -> Optional[str]:
        return str(self.data['function']) if 'function' in self.data and self.data['function'] is not None else None

    @property
    def line(self) -> Optional[int]:
        return int(self.data['line']) if 'line' in self.data and self.data['line'] is not None else None

    @property
    def message(self) -> Optional[str]:
        return str(self.data['message']) if 'message' in self.data and self.data['message'] is not None else None


__all__ = ['LogEvent']
