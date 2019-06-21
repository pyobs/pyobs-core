from .event import Event


class TaskStartedEvent(Event):
    def __init__(self, name: str = None, obs: str = None):
        Event.__init__(self)
        self.data = {'name': name, 'obs': obs}

    @property
    def name(self):
        return self.data['name']

    @property
    def obs(self):
        return self.data['obs']


__all__ = ['TaskStartedEvent']
