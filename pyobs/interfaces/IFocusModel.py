from .IStatus import IStatus


class IFocusModel(IStatus):
    def set_optimal_focus(self, *args, **kwargs):
        """Sets optimal focus.

        Raises:
            InterruptedError: If focus was interrupted.
        """
        raise NotImplementedError


__all__ = ['IFocusModel']
