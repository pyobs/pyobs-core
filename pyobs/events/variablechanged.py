from .event import Event


class VariableChangedEvent(Event):
    """Event to be sent when a variable has changed its value."""
    __module__ = 'pyobs.events'

    def __init__(self, name=None, value=None):
        Event.__init__(self)
        self.data = {'name': name, 'value': value}

    @property
    def name(self):
        return self.data['name']

    @property
    def value(self):
        return self.data['value']


__all__ = ['VariableChangedEvent']
