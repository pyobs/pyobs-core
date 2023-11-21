import logging
from typing import Any, Optional

from pyobs.images.processor import ImageProcessor
from pyobs.images import Image
from pyobs.utils.fits import FilenameFormatter


log = logging.getLogger(__name__)


class CreateFilename(ImageProcessor):
    """Formats the filename for an image and stores it in FNAME."""

    __module__ = "pyobs.images.processors.misc"

    _DEFAULT_PATTERN = "{SITEID}{TELID}-{INSTRUME}-{DAY-OBS|date:}-{FRAMENUM|string:04d}-{IMAGETYP|type}01.fits"

    def __init__(self, pattern: Optional[str], **kwargs: Any):
        """Init an image processor that adds a filename to an image.

        Args:
            pattern: Filename pattern.
        """
        ImageProcessor.__init__(self, **kwargs)

        if pattern is None:
            pattern = self._DEFAULT_PATTERN

        self._formatter = FilenameFormatter(pattern)

    async def __call__(self, image: Image) -> Image:
        """Add filename to image.

        Args:
            image: Image to add filename to.

        Returns:
            Image with filename in FNAME.
        """

        img = image.copy()
        img.format_filename(self._formatter)
        return img


__all__ = ["CreateFilename"]
