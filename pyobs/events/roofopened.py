from .event import Event


class RoofOpenedEvent(Event):
    """Event to be sent when the roof has finished opening."""
    __module__ = 'pyobs.events'

    def __init__(self):
        Event.__init__(self)


__all__ = ['RoofOpenedEvent']
