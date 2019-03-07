from .event import Event


class LogEvent(Event):
    def __init__(self, time=None, level=None, filename=None, function=None, line=None, message=None):
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
    def time(self):
        return self.data['time']

    @property
    def level(self):
        return self.data['level']

    @property
    def filename(self):
        return self.data['filename']

    @property
    def function(self):
        return self.data['function']

    @property
    def line(self):
        return self.data['line']

    @property
    def message(self):
        return self.data['message']


__all__ = ['LogEvent']
