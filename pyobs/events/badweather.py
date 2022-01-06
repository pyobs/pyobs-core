from .event import Event


class BadWeatherEvent(Event):
    """Event to be sent on bad weather."""

    __module__ = "pyobs.events"


__all__ = ["BadWeatherEvent"]
