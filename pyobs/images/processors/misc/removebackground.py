import logging
from typing import Any, Tuple

from pyobs.images.processor import ImageProcessor
from pyobs.images import Image
from pyobs.images.processors._daobackgroundremover import _DaoBackgroundRemover

log = logging.getLogger(__name__)


class RemoveBackground(ImageProcessor):
    """Remove background from image."""

    __module__ = "pyobs.images.processors.misc"

    def __init__(
        self,
        sigma: float = 3.0,
        box_size: Tuple[int, int] = (50, 50),
        filter_size: Tuple[int, int] = (3, 3),
        **kwargs: Any,
    ):
        """Init an image processor that removes background from image.

        Args:
            sigma: Sigma for clipping
            box_size: Box size for bkg estimation.
            filter_size: Size of filter.
        """
        ImageProcessor.__init__(self, **kwargs)

        self._background_remover = _DaoBackgroundRemover(sigma, box_size, filter_size)

    async def __call__(self, image: Image) -> Image:
        """Remove background from image.

        Args:
            image: Image to remove background from.

        Returns:
            Image without background.
        """

        return self._background_remover(image)


__all__ = ["RemoveBackground"]
