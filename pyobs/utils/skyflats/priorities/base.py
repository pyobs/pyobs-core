class SkyflatPriorities:
    """Base class for sky flat priorities."""
    __module__ = 'pyobs.utils.skyflats.priorities'

    def __call__(self):
        return {}


__all__ = ['SkyflatPriorities']
