from .interface import Interface


class ICalibrate(Interface):
    """
    Interface for devices that can be calibrated.
    """

    def calibrate(self, *args, **kwargs):
        """Calibrate the device."""
        raise NotImplementedError


__all__ = ['ICalibrate']
