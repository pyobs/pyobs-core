from .IStoppable import IStoppable


class IAutonomous(IStoppable):
    """Base class for all modules that act autonomously."""
    __module__ = 'pyobs.interfaces'
    pass


__all__ = ['IAutonomous']
