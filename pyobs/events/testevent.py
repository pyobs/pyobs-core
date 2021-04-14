from .event import Event


class TestEvent(Event):
    __module__ = 'pyobs.events'

    def __init__(self, message=None):
        Event.__init__(self)
        self.data['message'] = message

__all__ = ['TestEvent']
