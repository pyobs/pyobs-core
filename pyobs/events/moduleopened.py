from .event import Event


class ModuleOpenedEvent(Event):
    """Event to be sent when a module has opened."""

    __module__ = "pyobs.events"
    local = True


__all__ = ["ModuleOpenedEvent"]
