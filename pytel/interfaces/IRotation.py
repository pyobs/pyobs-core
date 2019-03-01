from .IMotionDevice import IMotionDevice


class IRotation(IMotionDevice):
    def set_rotation(self, angle, *args, **kwargs) -> bool:
        """ Sets the rotation angle to the given value in degrees. """
        raise NotImplementedError

    def get_rotation(self) -> float:
        """ Returns the current rotation angle. """
        raise NotImplementedError

    def track(self, ra: float, dec: float, *args, **kwargs) -> bool:
        """ Tracks the position angle of a rotator for an alt-az telescope. """
        raise NotImplementedError


__all__ = ['IRotation']
