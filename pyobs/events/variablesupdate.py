from .event import Event


class VariablesUpdateEvent(Event):
    """Event to be signal a variable update request."""
    __module__ = 'pyobs.events'

    def __init__(self, vars=None):
        Event.__init__(self)
        self.data = vars


__all__ = ['VariablesUpdateEvent']
