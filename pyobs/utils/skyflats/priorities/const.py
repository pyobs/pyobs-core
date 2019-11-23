from .base import SkyflatPriorities


class ConstSkyflatPriorities(SkyflatPriorities):
    def __init__(self, priorities: dict, *args, **kwargs):
        SkyflatPriorities.__init__(self)
        self.priorities = priorities


__all__ = ['ConstSkyflatPriorities']
