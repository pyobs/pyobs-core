from .interface import Interface


class ICalibrate(Interface):
    """The module can calibrate a device."""
    __module__ = 'pyobs.interfaces'

    def calibrate(self, *args, **kwargs):
        """Calibrate the device."""
        raise NotImplementedError


__all__ = ['ICalibrate']
