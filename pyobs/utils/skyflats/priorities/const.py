from .base import SkyflatPriorities


class ConstSkyflatPriorities(SkyflatPriorities):
    """Constant flat priorities."""
    __module__ = 'pyobs.utils.skyflats.priorities'

    def __init__(self, priorities: dict, *args, **kwargs):
        SkyflatPriorities.__init__(self)
        self._priorities = priorities

    def __call__(self):
        return self._priorities


__all__ = ['ConstSkyflatPriorities']
