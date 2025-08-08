import io
import logging
import os.path
from typing import Any

from pyobs.images.processor import ImageProcessor
from pyobs.images import Image
from pyobs.images.processors.annotation._pil import PILHelper
from pyobs.utils.fits import FilenameFormatter

log = logging.getLogger(__name__)


class SaveImage(ImageProcessor):
    """Broadcast image."""

    __module__ = "pyobs.images.processors.misc"

    def __init__(self, filename: str = "/pyobs/image.jpg", format: str | None = None, **kwargs: Any):
        """Init an image processor that saves an image as jpeg

        Args:
            filename: Filename to broadcast image.
            format: Explicitly set the image format to use.
        """
        ImageProcessor.__init__(self, **kwargs)

        self._formatter = FilenameFormatter(filename)
        self._image_format = format

    async def __call__(self, image: Image) -> Image:
        """Save image as jpeg.

        Args:
            image: Image to save.

        Returns:
            Original image.
        """
        filename = image.format_filename(self._formatter)

        image_format = self._image_format
        if image_format is None:
            image_format = os.path.splitext(filename)[1][1:].upper()
            if image_format == "JPG":
                image_format = "JPEG"
        print(image_format)

        im = PILHelper.from_image(image)
        with io.BytesIO() as bio:
            im.save(bio, format=image_format)
            await self.vfs.write_bytes(filename, bio.getvalue())

        return image


__all__ = ["SaveImage"]
