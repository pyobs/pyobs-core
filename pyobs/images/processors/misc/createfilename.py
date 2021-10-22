import logging

from pyobs.images.processor import ImageProcessor
from pyobs.images import Image
from pyobs.utils.fits import FilenameFormatter


log = logging.getLogger(__name__)


class CreateFilename(ImageProcessor):
    """Formats the filename for an image and stores it in FNAME."""
    __module__ = 'pyobs.images.processors.misc'

    def __init__(self, pattern: str, **kwargs:: Any):
        """Init an image processor that adds a filename to an image.

        Args:
            pattern: Filename pattern.
        """
        ImageProcessor.__init__(self, **kwargs)

        # default filename patterns
        if pattern is None:
            pattern = '{SITEID}{TELID}-{INSTRUME}-{DAY-OBS|date:}-{FRAMENUM|string:04d}-{IMAGETYP|type}01.fits'
        self._formatter = FilenameFormatter(pattern)

    def __call__(self, image: Image) -> Image:
        """Add filename to image.

        Args:
            image: Image to add filename to.

        Returns:
            Image with filename in FNAME.
        """

        # copy image and set filename
        img = image.copy()
        img.format_filename(self._formatter)
        return img


__all__ = ['CreateFilename']

