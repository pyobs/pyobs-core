from .event import Event


class TestEvent(Event):
    """Just a test event."""
    __module__ = 'pyobs.events'

    def __init__(self, message: Optional[str] = None):
        Event.__init__(self)
        self.data['message'] = message


__all__ = ['TestEvent']
