from .event import Event


class ModuleOpenedEvent(Event):
    __module__ = 'pyobs.events'
    local = True

    def __init__(self):
        Event.__init__(self)


__all__ = ['ModuleOpenedEvent']
