from abc import ABCMeta, abstractmethod
from typing import Any

from .IAbortable import IAbortable
from .IImageGrabber import IImageGrabber
from pyobs.utils.enums import ExposureStatus


class ICamera(IAbortable, IImageGrabber, metaclass=ABCMeta):
    """The module controls a camera."""

    __module__ = "pyobs.interfaces"

    @abstractmethod
    async def get_exposure_status(self, **kwargs: Any) -> ExposureStatus:
        """Returns the current status of the camera, which is one of 'idle', 'exposing', or 'readout'.

        Returns:
            Current status of camera.
        """
        ...

    @abstractmethod
    async def abort(self, **kwargs: Any) -> None:
        """Aborts the current exposure and sequence.

        Raises:
            ValueError: If exposure could not be aborted.
        """
        ...

    @abstractmethod
    async def get_exposure_progress(self, **kwargs: Any) -> float:
        """Returns the progress of the current exposure in percent.

        Returns:
            Progress of the current exposure in percent.
        """
        ...


__all__ = ["ICamera"]
