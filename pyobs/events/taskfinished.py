from .event import Event


class TaskFinishedEvent(Event):
    def __init__(self, name: str = None):
        Event.__init__(self)
        self.data = name

    @property
    def name(self):
        return self.data


__all__ = ['TaskFinishedEvent']
