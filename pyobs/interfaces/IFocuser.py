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

    def set_focus_offset(self, offset: float, *args, **kwargs):
        """Sets focus offset.

        Args:
            offset: New focus offset.

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

    def get_focus_offset(self, *args, **kwargs) -> float:
        """Return current focus offset.

        Returns:
            Current focus offset.
        """
        raise NotImplementedError

__all__ = ['IFocuser']
