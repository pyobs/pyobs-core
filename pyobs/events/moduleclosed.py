from .event import Event


class ModuleClosedEvent(Event):
    local = True

    def __init__(self):
        Event.__init__(self)


__all__ = ['ModuleClosedEvent']
