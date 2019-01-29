from .event import Event


class RoofClosingEvent(Event):
    def __init__(self):
        Event.__init__(self)


__all__ = ['RoofClosingEvent']
