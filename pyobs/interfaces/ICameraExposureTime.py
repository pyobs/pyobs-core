from .interface import *


class ICameraExposureTime(Interface):
    """The camera supports exposure times, to be used together with :class:`~pyobs.interfaces.ICamera`."""
    __module__ = 'pyobs.interfaces'

    def set_exposure_time(self, exposure_time: float, *args, **kwargs):
        """Set the exposure time in seconds.

        Args:
            exposure_time: Exposure time in seconds.

        Raises:
            ValueError: If exposure time could not be set.
        """
        raise NotImplementedError

    def get_exposure_time(self, *args, **kwargs) -> float:
        """Returns the exposure time in seconds.

        Returns:
            Exposure time in seconds.
        """
        raise NotImplementedError

    def get_exposure_time_left(self, *args, **kwargs) -> float:
        """Returns the remaining exposure time on the current exposure in seconds.

        Returns:
            Remaining exposure time in seconds.
        """
        raise NotImplementedError


__all__ = ['ICameraExposureTime']
