import logging
from typing import Any

from pyobs.events import NewImageEvent
from pyobs.images.processor import ImageProcessor
from pyobs.images import Image
from pyobs.utils.enums import ImageType
from pyobs.utils.fits import FilenameFormatter

log = logging.getLogger(__name__)


class Save(ImageProcessor):
    """Broadcast image."""

    __module__ = "pyobs.images.processors.misc"

    def __init__(self, filename: str = "/pyobs/image.fits", broadcast: bool = False, **kwargs: Any):
        """Init an image processor that broadcasts an image

        Args:
            filename: Filename to broadcast image.
        """
        ImageProcessor.__init__(self, **kwargs)

        self._formatter = FilenameFormatter(filename)
        self._broadcast = broadcast

    async def open(self) -> None:
        """Initialize processor."""
        await ImageProcessor.open(self)

        if self._broadcast and self.comm is not None:
            await self.comm.register_event(NewImageEvent)

    async def __call__(self, image: Image) -> Image:
        """Broadcast image.

        Args:
            image: Image to broadcast.

        Returns:
            Original image.
        """

        filename = image.format_filename(self._formatter)
        await self.vfs.write_image(filename, image)
        if self._broadcast:
            await self.comm.send_event(NewImageEvent(filename, image_type=ImageType(image.header["IMAGETYP"])))
        return image


__all__ = ["Save"]
