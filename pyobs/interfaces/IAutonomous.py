from .IStartStop import IStartStop


class IAutonomous(IStartStop):
    """The module does some autonomous actions, mainly used for warnings to users."""
    __module__ = 'pyobs.interfaces'
    pass


__all__ = ['IAutonomous']
