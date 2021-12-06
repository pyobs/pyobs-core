from typing import Any

from .IImageGrabber import IImageGrabber


class IVideo(IImageGrabber):
    """The module controls a video streaming device."""
    __module__ = 'pyobs.interfaces'

    async def get_video(self, **kwargs: Any) -> str:
        """Returns path to video.

        Returns:
            Path to video.
        """
        raise NotImplementedError


__all__ = ['IVideo']
