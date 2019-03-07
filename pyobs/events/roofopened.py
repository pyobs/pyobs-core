from .event import Event


class RoofOpenedEvent(Event):
    def __init__(self):
        Event.__init__(self)


__all__ = ['RoofOpenedEvent']
