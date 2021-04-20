from .IStoppable import IStoppable


class IAutonomous(IStoppable):
    """The module does some autonomous actions, mainly used for warnings to users."""
    __module__ = 'pyobs.interfaces'
    pass


__all__ = ['IAutonomous']
