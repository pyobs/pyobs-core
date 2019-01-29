from .IStatus import IStatus


class IFocusModel(IStatus):
    def set_optimal_focus(self, *args, **kwargs) -> bool:
        """sets optimal focus"""
        raise NotImplementedError


__all__ = ['IFocusModel']
