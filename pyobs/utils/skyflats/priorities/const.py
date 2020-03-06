from .base import SkyflatPriorities


class ConstSkyflatPriorities(SkyflatPriorities):
    def __init__(self, priorities: dict, *args, **kwargs):
        SkyflatPriorities.__init__(self)
        self._priorities = priorities

    def __call__(self):
        return self._priorities


__all__ = ['ConstSkyflatPriorities']
