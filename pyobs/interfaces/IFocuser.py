from .IMotion import IMotion


class IFocuser(IMotion):
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


__all__ = ['IFocuser']
