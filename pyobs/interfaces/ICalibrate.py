from .interface import Interface


class ICalibrate(Interface):
    """Interface for devices that can be calibrated."""
    __module__ = 'pyobs.interfaces'

    def calibrate(self, *args, **kwargs):
        """Calibrate the device."""
        raise NotImplementedError


__all__ = ['ICalibrate']
