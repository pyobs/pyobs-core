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
    """Download an image from a URL."""

    __module__ = "pyobs.images.processors.misc"

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
