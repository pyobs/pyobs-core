from .event import Event


class FilterChangedEvent(Event):
    __module__ = 'pyobs.events'

    def __init__(self, current: str = None):
        Event.__init__(self)
        self.data = current

    @property
    def filter(self):
        return self.data


__all__ = ['FilterChangedEvent']
