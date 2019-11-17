from .IStoppable import IStoppable


class IAutoGuiding(IStoppable):
    def set_exposure_time(self, exp_time: int):
        """Set the exposure time for the auto-guider.

        Args:
            exp_time: Exposure time in ms.
        """
        raise NotImplementedError


__all__ = ['IAutoGuiding']
