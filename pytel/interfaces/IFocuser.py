from .IStatus import IStatus


class IFocuser(IStatus):
    def set_focus(self, focus: float, *args, **kwargs) -> bool:
        """sets focus"""
        raise NotImplementedError

    def get_focus(self, *args, **kwargs) -> float:
        """returns focus"""
        raise NotImplementedError

    def status(self, *args, **kwargs) -> dict:
        """Returns current status.
        Returns:
            dict: A dictionary that should contain at least the following fields:

                IFocuser:
                    Focus (float):  Current focus value.
        """
        raise NotImplementedError


__all__ = ['IFocuser']
