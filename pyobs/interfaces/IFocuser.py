from .IMotion import IMotion


class IFocuser(IMotion):
    """Generic focussing device with states corresponding to IMotionDevice.MotionState.

    Other interfaces to be implemented:
        (none)
    """

    def init(self, *args, **kwargs):
        """Initialize device.

        Raises:
            ValueError: If device could not be initialized.
        """
        raise NotImplementedError

    def park(self, *args, **kwargs):
        """Park device.

        Raises:
            ValueError: If device could not be parked.
        """
        raise NotImplementedError

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

    def get_motion_status(self, device: str = None) -> IMotion.Status:
        """Returns current motion status.

        Args:
            device: Name of device to get status for, or None.

        Returns:
            A string from the Status enumerator.
        """
        raise NotImplementedError


__all__ = ['IFocuser']
