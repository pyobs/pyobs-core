from .event import Event


class VariablesUpdateEvent(Event):
    __module__ = 'pyobs.events'

    def __init__(self, vars=None):
        Event.__init__(self)
        self.data = vars


__all__ = ['VariablesUpdateEvent']
