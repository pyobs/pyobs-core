import abc
import logging
import os
from datetime import datetime
from typing import Any
import aiohttp
import numpy as np

from pyobs.images.processor import ImageProcessor
from pyobs.images import Image


log = logging.getLogger(__name__)


class ImageConverter(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def __call__(self, image_data: bytes) -> Image:
        pass


class EncodedImageConverter(ImageConverter):
    def __call__(self, image_data: bytes) -> Image:
        img_array = np.asarray(bytearray(image_data), dtype=np.uint8)

        import cv2

        bgr_data = cv2.imdecode(img_array, cv2.IMREAD_UNCHANGED)
        data = cv2.cvtColor(bgr_data, cv2.COLOR_BGR2RGB)

        # 3D, i.e. color, image?
        if len(data.shape) == 3:
            # we need three images of uint8 format
            if data.shape[0] != 3 and data.shape[2] != 3:
                raise ValueError("Data cubes only supported with three layers, which are interpreted as RGB.")
            if data.shape[2] == 3:
                # move axis
                data = np.moveaxis(data, 2, 0)

        image = Image(data=data)  # type: ignore
        image.header["DATE-OBS"] = datetime.now().isoformat()
        image.header["EXPTIME"] = 0

        return image


class FitsImageConverter(ImageConverter):
    def __call__(self, image_data: bytes) -> Image:
        return Image.from_bytes(image_data)


class Download(ImageProcessor):
    """
    Download an image from an HTTP(S) URL and return it as a :class:`pyobs.images.Image`.

    This processor uses :mod:`aiohttp` to fetch image bytes from the configured
    ``url`` and converts them into a :class:`pyobs.images.Image`. The conversion is chosen
    automatically based on the URL's filename extension:

    - ``.fits`` files are parsed with :meth:`pyobs.images.Image.from_bytes`, preserving their FITS header.
    - Other common image formats (e.g., PNG, JPEG) are decoded via OpenCV and converted to RGB.
      For 3-channel color images, the channel axis is moved to the front (``C, H, W``) and basic
      header cards are set (``DATE-OBS`` and ``EXPTIME=0``).

    The input argument to ``__call__`` is ignored; the processor always downloads and returns a new image.

    :param str url:
        The HTTP(S) URL to download. The file type is inferred from the URL's extension
        using :func:`os.path.splitext`; ``.fits`` triggers FITS parsing, all other extensions
        are treated as encoded images to be decoded via OpenCV.
    :param kwargs:
        Additional keyword arguments forwarded to :class:`pyobs.images.processor.ImageProcessor`.

    Behavior
    --------
    - Performs an HTTP GET request to ``url`` using :class:`aiohttp.ClientSession`.
    - If the URL ends with ``.fits``, the image is constructed with :meth:`pyobs.images.Image.from_bytes`,
      preserving existing FITS headers.
    - Otherwise, the image is decoded with OpenCV:
      - Bytes are passed to ``cv2.imdecode`` (with ``cv2.IMREAD_UNCHANGED``), then converted from BGR to RGB.
      - For 3-channel color images, the channel axis is moved to the front (``C, H, W``).
      - The processor sets ``DATE-OBS`` to the current ISO timestamp and ``EXPTIME`` to ``0`` in the header.
    - The input parameter ``image`` to ``__call__`` is ignored (no-op); a new image object is returned.

    Input/Output
    ------------
    - Input: :class:`pyobs.images.Image` (ignored).
    - Output: :class:`pyobs.images.Image` constructed from the downloaded bytes.

    Configuration (YAML)
    --------------------
    .. code-block:: yaml

       class: pyobs.images.processors.image.Download
       url: "https://example.org/data/image.fits"

    Decoding a JPEG/PNG (requires OpenCV):

    .. code-block:: yaml

       class: pyobs.images.processors.image.Download
       url: "https://example.org/data/preview.jpg"

    Notes
    -----
    - File type detection is based on the URL's extension. If the URL does not reflect the true format
      (e.g., a FITS file served without a ``.fits`` suffix), decoding may fail or produce unintended results.
    - For encoded images, only minimal FITS-like header information is set. If you need full metadata,
      prefer FITS sources or augment headers downstream.
    """

    __module__ = "pyobs.images.processors.image"

    def __init__(self, url: str, **kwargs: Any):
        """Init a new software binning pipeline step.

        Args:
            binning: Binning to apply to image.
        """
        ImageProcessor.__init__(self, **kwargs)

        # store
        self._url = url

        # what file do we have?
        file_type = os.path.splitext(url)[1]
        self._converter: ImageConverter
        if file_type == ".fits":
            self._converter = FitsImageConverter()
        else:
            self._converter = EncodedImageConverter()

    async def __call__(self, image: Image) -> Image:
        """Download an image.

        Args:
            image: Whatever is passed will be ignored.

        Returns:
            Downloaded image.
        """

        async with aiohttp.ClientSession() as session:
            async with session.get(self._url) as response:
                response.raise_for_status()
                image_data = await response.read()
                return self._converter(image_data)


__all__ = ["Download"]
