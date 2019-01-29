from .event import Event


class BadWeatherEvent(Event):
    def __init__(self):
        Event.__init__(self)


__all__ = ['BadWeatherEvent']
