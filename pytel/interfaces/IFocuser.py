from .IMoving import IMoving


class IFocuser(IMoving):
    """Generic focussing device with states corresponding to IMotionDevice.MotionState.

    Other interfaces to be implemented:
        (none)
    """

    def set_focus(self, focus: float, *args, **kwargs):
        """Sets new focus.

        Args:
            focus: New focus value.

        Raises:
            InterruptedError: If focus was interrupted.
        """
        raise NotImplementedError

    def get_focus(self, *args, **kwargs) -> float:
        """Return current focus.

        Returns:
            Current focus.
        """
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
