from .event import Event


class ModuleClosedEvent(Event):
    """Event to be sent when a module has closed."""
    __module__ = 'pyobs.events'
    local = True

    def __init__(self):
        Event.__init__(self)


__all__ = ['ModuleClosedEvent']
