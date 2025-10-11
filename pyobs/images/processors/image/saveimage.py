import io
import logging
import os.path
from typing import Any

from pyobs.images.processor import ImageProcessor
from pyobs.images import Image
from pyobs.images.processors.annotation._pillow import PillowHelper
from pyobs.utils.fits import FilenameFormatter

log = logging.getLogger(__name__)


class SaveImage(ImageProcessor):
    """
    Save an image as an encoded byte stream (e.g., JPEG, PNG) via the virtual file system.

    This asynchronous processor formats a destination filename using a
    :class:`pyobs.utils.formatter.FilenameFormatter`, encodes the input
    :class:`pyobs.images.Image` to the desired image format using Pillow, and writes
    the resulting bytes to the pyobs virtual file system (``vfs``). The original image
    object is returned unchanged.

    :param str filename: Filename template for saving the encoded image. The actual path is
                         produced by :meth:`pyobs.images.Image.format_filename` using a
                         :class:`FilenameFormatter`. The file extension is used to infer
                         the image format if ``format`` is not provided. Default: ``"/pyobs/image.jpg"``.
    :param str format: Explicit image format to use for encoding (e.g., ``"JPEG"``, ``"PNG"``,
                       ``"TIFF"``). If ``None``, the format is inferred from the filename extension.
                       Default: ``None``.
    :param kwargs: Additional keyword arguments forwarded to
                   :class:`pyobs.images.processor.ImageProcessor`.

    Behavior
    --------
    - Computes the target path via ``image.format_filename(self._formatter)``.
    - Encodes the image to bytes using :meth:`SaveImage.encode_image`, which leverages Pillow:
      - If ``format`` is ``None``, the format is inferred from the filename extension
        (uppercased) with a special case mapping ``JPG -> JPEG``.
      - Conversion from :class:`pyobs.images.Image` to a Pillow image is performed by
        :class:`pyobs.utils.image.PillowHelper`.
    - Writes the encoded bytes to the virtual file system using ``self.vfs.write_bytes(filename, data)``.
    - Returns the original image without modification.

    Input/Output
    ------------
    - Input: :class:`pyobs.images.Image`
    - Output: :class:`pyobs.images.Image` (unchanged), with side effect of writing encoded
      bytes to the virtual file system at the formatted path.

    Configuration (YAML)
    --------------------
    Save as JPEG inferred from extension:

    .. code-block:: yaml

       class: pyobs.images.processors.misc.SaveImage
       filename: "/pyobs/latest.jpg"

    Explicitly set format (overrides extension):

    .. code-block:: yaml

       class: pyobs.images.processors.misc.SaveImage
       filename: "/data/snapshot.out"
       format: "PNG"

    Notes
    -----
    - Format inference is based on the filename extension. If the extension is ``.jpg``,
      it is mapped to Pillow's ``"JPEG"`` format.
    - Ensure the image is convertible to a Pillow image; the helper is responsible for
      handling channel order and dtype conversions.
    - Errors from the virtual file system (e.g., write failures) or Pillow (unsupported format)
      propagate to the caller.
    - This processor is asynchronous; call it within an event loop (using ``await``).
    """

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
        data = self.encode_image(image, filename, self._image_format)
        await self.vfs.write_bytes(filename, data)
        return image

    @staticmethod
    def encode_image(image: Image, filename: str, image_format: str | None = None) -> bytes:
        if image_format is None:
            image_format = os.path.splitext(filename)[1][1:].upper()
            if image_format == "JPG":
                image_format = "JPEG"

        im = PillowHelper.from_image(image)
        with io.BytesIO() as bio:
            im.save(bio, format=image_format)
            return bio.getvalue()


__all__ = ["SaveImage"]
