import logging
from typing import Any

from pyobs.events import NewImageEvent
from pyobs.images.processor import ImageProcessor
from pyobs.images import Image
from pyobs.utils.enums import ImageType
from pyobs.utils.fits import FilenameFormatter

log = logging.getLogger(__name__)


class Save(ImageProcessor):
    """
    Save an image to the virtual file system and optionally broadcast a NewImageEvent.

    This processor formats a destination filename using a
    :class:`pyobs.utils.formatter.FilenameFormatter` (configured via ``filename``),
    writes the image to the pyobs virtual file system (``vfs``), and, if enabled,
    broadcasts a :class:`NewImageEvent` via the communication interface (``comm``).
    The original image is returned unchanged.

    :param str filename: Filename template for saving the image. The actual path is produced by
                         :meth:`pyobs.images.Image.format_filename` using a
                         :class:`FilenameFormatter`. Default: ``"/pyobs/image.fits"``.
    :param bool broadcast: If ``True``, broadcast a :class:`NewImageEvent` after saving the image.
                           Default: ``False``.
    :param kwargs: Additional keyword arguments forwarded to
                   :class:`pyobs.images.processor.ImageProcessor`.

    Behavior and requirements
    -------------------------
    - The processor requires a configured virtual file system (``self.vfs``) to persist images.
    - Broadcasting requires a communication interface (``self.comm``) and successful registration
      of ``NewImageEvent`` in ``open()``.
    - The broadcasted event’s ``image_type`` is derived from the FITS header key ``IMAGETYP``.
      This key must be present and convertible to :class:`ImageType`; otherwise, an exception may be raised.

    Input/Output
    ------------
    - Input: :class:`pyobs.images.Image`
    - Output: :class:`pyobs.images.Image` (unchanged), with side effects:

      - Image is saved to the virtual file system.
      - Optional event broadcast after saving.

    Configuration (YAML)
    --------------------
    Save and broadcast new images:

    .. code-block:: yaml

       class: pyobs.images.processors.misc.Save
       filename: "/pyobs/image.fits"
       broadcast: true

    Save only:

    .. code-block:: yaml

       class: pyobs.images.processors.misc.Save
       filename: "/data/latest.fits"
       broadcast: false

    Notes
    -----
    - Ensure the image header contains a valid ``IMAGETYP`` if broadcasting is enabled.
    - The actual filename may include formatted components depending on your
      :class:`FilenameFormatter` and :meth:`pyobs.images.Image.format_filename` implementation.
    - Errors raised by the virtual file system (e.g., write failures) or communication subsystem
      (e.g., event dispatch errors) propagate to the caller.
    """

    __module__ = "pyobs.images.processors.image"

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
