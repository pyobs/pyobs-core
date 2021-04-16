from .event import Event


class BadWeatherEvent(Event):
    """Event to be sent on bad weather."""
    __module__ = 'pyobs.events'

    def __init__(self):
        Event.__init__(self)


__all__ = ['BadWeatherEvent']
