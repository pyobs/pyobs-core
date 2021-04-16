from .event import Event


class InitializedEvent(Event):
    """Event to be sent when a device has been initialized."""
    __module__ = 'pyobs.events'

    def __init__(self):
        Event.__init__(self)


__all__ = ['InitializedEvent']
