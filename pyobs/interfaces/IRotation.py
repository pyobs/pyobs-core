from .IMotion import IMotion


class IRotation(IMotion):
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

    def set_rotation(self, angle, *args, **kwargs):
        """ Sets the rotation angle to the given value in degrees. """
        raise NotImplementedError

    def get_rotation(self) -> float:
        """ Returns the current rotation angle. """
        raise NotImplementedError

    def track(self, ra: float, dec: float, *args, **kwargs):
        """ Tracks the position angle of a rotator for an alt-az telescope. """
        raise NotImplementedError


__all__ = ['IRotation']
