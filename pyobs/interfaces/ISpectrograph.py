from abc import ABCMeta
from typing import Any

from .IAbortable import IAbortable
from pyobs.utils.enums import ExposureStatus


class ISpectrograph(IAbortable, metaclass=ABCMeta):
    """The module controls a camera."""
    __module__ = 'pyobs.interfaces'

    async def get_exposure_status(self, **kwargs: Any) -> ExposureStatus:
        """Returns the current status of the camera, which is one of 'idle', 'exposing', or 'readout'.

        Returns:
            Current status of camera.
        """
        raise NotImplementedError

    async def grab_spectrum(self, broadcast: bool = True, **kwargs: Any) -> str:
        """Grabs a spectrum and returns reference.

        Args:
            broadcast: Broadcast existence of image.

        Returns:
            Name of image that was taken.
        """
        raise NotImplementedError

    async def abort(self, **kwargs: Any) -> None:
        """Aborts the current exposure.

        Raises:
            ValueError: If exposure could not be aborted.
        """
        raise NotImplementedError

    async def get_exposure_progress(self, **kwargs: Any) -> float:
        """Returns the progress of the current exposure in percent.

        Returns:
            Progress of the current exposure in percent.
        """
        raise NotImplementedError


__all__ = ['ISpectrograph']
