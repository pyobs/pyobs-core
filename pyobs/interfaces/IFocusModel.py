from .interface import Interface


class IFocusModel(Interface):
    """The module provides a model for the telescope focus, e.g. based on temperatures."""
    __module__ = 'pyobs.interfaces'

    def get_optimal_focus(self, *args, **kwargs) -> float:
        """Returns the optimal focus."""
        raise NotImplementedError

    def set_optimal_focus(self, *args, **kwargs):
        """Sets optimal focus."""
        raise NotImplementedError


__all__ = ['IFocusModel']
