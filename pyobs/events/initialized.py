from .event import Event


class InitializedEvent(Event):
    def __init__(self):
        Event.__init__(self)


__all__ = ['InitializedEvent']
