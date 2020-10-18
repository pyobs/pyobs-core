from .IStoppable import IStoppable


class IAutonomous(IStoppable):
    """Base class for all modules that act autonomously."""
    pass


__all__ = ['IAutonomous']
