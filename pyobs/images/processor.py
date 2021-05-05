from typing import Any

from pyobs.images import Image


class ImageProcessor:
    def __call__(self, image: Image) -> Any:
        """Processes an image.

        Args:
            image: Image to process.

        Returns:
            Whatever the process wants to return.
        """
        raise NotImplementedError


__all__ = ['ImageProcessor']
