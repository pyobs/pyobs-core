from typing import Dict, Tuple, Any

from .base import SkyflatPriorities


class ConstSkyflatPriorities(SkyflatPriorities):
    """Constant flat priorities."""
    __module__ = 'pyobs.utils.skyflats.priorities'

    def __init__(self, priorities: Dict[Tuple[str, Tuple[int, int]], float], *args: Any, **kwargs: Any):
        SkyflatPriorities.__init__(self)
        self._priorities = priorities

    def __call__(self) -> Dict[Tuple[str, Tuple[int, int]], float]:
        return self._priorities


__all__ = ['ConstSkyflatPriorities']
