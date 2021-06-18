from .interface import Interface


class IWebcam(Interface):
    """The module controls a camera."""
    __module__ = 'pyobs.interfaces'

    def get_next_frame(self, *args, **kwargs) -> str:
        """Waits for next frame, saves it and returns filename.

        Returns:
            Filename for last exposure.
        """


__all__ = ['IWebcam']
