from typing import Any

from .IStartStop import IStartStop


class IAutoGuiding(IStartStop):
    """The module can perform auto-guiding."""
    __module__ = 'pyobs.interfaces'

    def set_exposure_time(self, exposure_time: float, **kwargs: Any) -> None:
        """Set the exposure time for the auto-guider.

        Args:
            exposure_time: Exposure time in secs.
        """
        raise NotImplementedError


__all__ = ['IAutoGuiding']
