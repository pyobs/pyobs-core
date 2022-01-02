from abc import ABCMeta, abstractmethod
from typing import Any

from pyobs.images import Image
from pyobs.object import Object


class ImageProcessor(Object, metaclass=ABCMeta):
    def __init__(self, **kwargs: Any):
        """Init new image processor."""
        Object.__init__(self, **kwargs)

    @abstractmethod
    async def __call__(self, image: Image) -> Image:
        """Processes an image.

        Args:
            image: Image to process.

        Returns:
            Processed image.
        """
        ...

    async def reset(self) -> None:
        """Resets state of image processor"""
        pass


__all__ = ["ImageProcessor"]
