from .event import Event


class RoofOpenedEvent(Event):
    """Event to be sent when the roof has finished opening."""

    __module__ = "pyobs.events"


__all__ = ["RoofOpenedEvent"]
