import enum

from .IAbortable import IAbortable


class ICamera(IAbortable):
    """Basic interface for all cameras."""

    class ExposureStatus(enum.Enum):
        """Enumerator for camera status."""
        IDLE = 'idle'
        EXPOSING = 'exposing'
        READOUT = 'readout'

    class ImageType(enum.Enum):
        """Enumerator specifying the image type."""
        BIAS = 'bias'
        DARK = 'dark'
        OBJECT = 'object'
        SKYFLAT = 'skyflat'
        FOCUS = 'focus'
        ACQUISITION = 'acquisition'

    def get_exposure_status(self, *args, **kwargs) -> ExposureStatus:
        """Returns the current status of the camera, which is one of 'idle', 'exposing', or 'readout'.

        Returns:
            Current status of camera.
        """
        raise NotImplementedError

    def expose(self, exposure_time: int, image_type: ImageType, broadcast: bool = True, *args, **kwargs) -> str:
        """Starts exposure and returns reference to image.

        Args:
            exposure_time: Exposure time in seconds.
            image_type: Type of image.
            broadcast: Broadcast existence of image.

        Returns:
            Name of image that was taken.
        """
        raise NotImplementedError

    def abort(self, *args, **kwargs):
        """Aborts the current exposure and sequence.

        Raises:
            ValueError: If exposure could not be aborted.
        """
        raise NotImplementedError

    def get_exposure_time_left(self, *args, **kwargs) -> float:
        """Returns the remaining exposure time on the current exposure in ms.

        Returns:
            Remaining exposure time in ms.
        """
        raise NotImplementedError

    def get_exposure_progress(self, *args, **kwargs) -> float:
        """Returns the progress of the current exposure in percent.

        Returns:
            Progress of the current exposure in percent.
        """
        raise NotImplementedError


__all__ = ['ICamera']
