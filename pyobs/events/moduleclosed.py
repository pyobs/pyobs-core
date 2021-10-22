from .event import Event


class ModuleClosedEvent(Event):
    """Event to be sent when a module has closed."""
    __module__ = 'pyobs.events'
    local = True


__all__ = ['ModuleClosedEvent']
