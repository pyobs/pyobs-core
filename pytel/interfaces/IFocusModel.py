from .IStatus import IStatus


class IFocusModel(IStatus):
    def set_optimal_focus(self, *args, **kwargs) -> bool:
        """Sets optimal focus.

        Returns:
            Success or not.
        """
        raise NotImplementedError


__all__ = ['IFocusModel']
