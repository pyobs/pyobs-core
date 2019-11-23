from .base import Priorities


class ConstSkyflatPriorities(Priorities):
    def __init__(self, priorities: dict, *args, **kwargs):
        Priorities.__init__(self)
        self.priorities = priorities


__all__ = ['ConstSkyflatPriorities']
