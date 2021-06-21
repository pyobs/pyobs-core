from .IImageGrabber import IImageGrabber


class IWebcam(IImageGrabber):
    """The module controls a camera."""
    __module__ = 'pyobs.interfaces'

    def get_video(self, *args, **kwargs) -> str:
        """Returns path to video.

        Returns:
            Path to video.
        """
        raise NotImplementedError


__all__ = ['IWebcam']
