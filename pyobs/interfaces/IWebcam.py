from .interface import Interface


class IWebcam(Interface):
    """The module controls a camera."""
    __module__ = 'pyobs.interfaces'

    def wait_for_frame(self, *args, **kwargs):
        """Wait for next frame that starts after this method has been called."""
        raise NotImplementedError

    def get_last_frame(self, *args, **kwargs) -> str:
        """Returns filename of last frame.

        Returns:
            Filename for last exposure.
        """
        raise NotImplementedError


__all__ = ['IWebcam']
