from abc import ABCMeta, abstractmethod
from typing import Any

from .IData import IData


class IVideo(IData, metaclass=ABCMeta):
    """The module controls a video streaming device."""

    __module__ = "pyobs.interfaces"

    @abstractmethod
    async def get_video(self, **kwargs: Any) -> str:
        """Returns path to video.

        Returns:
            Path to video.
        """
        ...


__all__ = ["IVideo"]
