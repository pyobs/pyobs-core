from typing import Dict, Tuple


class SkyflatPriorities:
    """Base class for sky flat priorities."""
    __module__ = 'pyobs.utils.skyflats.priorities'

    def __call__(self) -> Dict[Tuple[str, Tuple[int, int]], float]:
        return {}


__all__ = ['SkyflatPriorities']
