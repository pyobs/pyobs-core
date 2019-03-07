from .event import Event


class TestEvent(Event):
    def __init__(self, message=None):
        Event.__init__(self)
        self.data['message'] = message

__all__ = ['TestEvent']
