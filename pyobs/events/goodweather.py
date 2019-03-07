from .event import Event


class GoodWeatherEvent(Event):
    def __init__(self):
        Event.__init__(self)


__all__ = ['GoodWeatherEvent']
