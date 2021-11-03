from .event import Event


class InitializedEvent(Event):
    """Event to be sent when a device has been initialized."""
    __module__ = 'pyobs.events'


__all__ = ['InitializedEvent']
