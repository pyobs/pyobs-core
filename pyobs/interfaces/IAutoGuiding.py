from .IStoppable import IStoppable


class IAutoGuiding(IStoppable):
    __module__ = 'pyobs.interfaces'

    def set_exposure_time(self, exposure_time: float, *args, **kwargs):
        """Set the exposure time for the auto-guider.

        Args:
            exposure_time: Exposure time in secs.
        """
        raise NotImplementedError


__all__ = ['IAutoGuiding']
