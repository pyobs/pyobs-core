from .event import Event


class RoofClosingEvent(Event):
    """Event to be sent when the roof starts closing."""
    __module__ = 'pyobs.events'

    def __init__(self):
        Event.__init__(self)


__all__ = ['RoofClosingEvent']
