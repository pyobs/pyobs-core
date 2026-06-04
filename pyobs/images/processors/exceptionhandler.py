import logging
from typing import Union, Dict, Any, Optional

from pyobs.images import ImageProcessor, Image
from pyobs.object import get_object

import pyobs.utils.exceptions as exc
log = logging.getLogger(__name__)


class ExceptionHandler(ImageProcessor):

    __module__ = "pyobs.images.processors"

    def __init__(self, processor: Union[ImageProcessor, Dict[str, Any]], error_header: Optional[str] = None) -> None:
        super().__init__()

        self._processor: ImageProcessor = get_object(processor, ImageProcessor)  # type: ignore
        self._error_header = error_header

    async def __call__(self, image: Image) -> Image:
        try:
            return await self._processor(image)
        except exc.ImageError as e:
            return await self._handle_error(image, e)

    async def _handle_error(self, image: Image, error: exc.ImageError) -> Image:
        log.warning(error.message)

        output_image = image.copy()

        if self._error_header is not None:
            output_image.header[self._error_header] = 1

        return output_image

    async def reset(self) -> None:
        await self._processor.reset()


__all__ = ["ExceptionHandler"]
