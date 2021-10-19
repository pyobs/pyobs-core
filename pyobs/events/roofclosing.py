from .event import Event


class RoofClosingEvent(Event):
    """Event to be sent when the roof starts closing."""
    __module__ = 'pyobs.events'


__all__ = ['RoofClosingEvent']
