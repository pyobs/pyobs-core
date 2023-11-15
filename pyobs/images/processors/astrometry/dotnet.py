import logging
from typing import Any

import pyobs.utils.exceptions as exc
from pyobs.images import Image
from ._dotnet_request_builder import _DotNetRequestBuilder
from ._dotnet_request_logger import _RequestLogger
from ._dotnet_response_saver import _ResponseImageWriter
from .astrometry import Astrometry

log = logging.getLogger(__name__)


class AstrometryDotNet(Astrometry):
    """Perform astrometry using astrometry.net"""

    __module__ = "pyobs.images.processors.astrometry"

    def __init__(
        self,
        url: str,
        source_count: int = 50,
        radius: float = 3.0,
        timeout: int = 10,
        exceptions: bool = True,
        **kwargs: Any,
    ):
        """Init new astronomy.net processor.

        Args:
            url: URL to service.
            source_count: Number of sources to send.
            radius: Radius to search in.
            timeout: Timeout in seconds for call to astrometry web service.
            exceptions: Whether to raise Exceptions.
        """
        Astrometry.__init__(self, **kwargs)

        self.url = url

        self.timeout = timeout
        self.exceptions = exceptions

        self._request_builder = _DotNetRequestBuilder(source_count, radius)

    async def _process(self, image: Image) -> Image:
        # build the request
        request = self._request_builder(image)

        logger = _RequestLogger(log, image, request.request_data)
        logger.log_request_data()

        await request.send(self.url, self.timeout)

        response_writer = _ResponseImageWriter(request.response_data, image)
        result_image = response_writer()

        logger.log_request_result(response_writer.image_wcs)

        return result_image

    def _handle_error(self, image: Image, error: exc.ImageError):
        if self.exceptions:
            raise error

        image.header["WCSERR"] = 1

        log.warning(error.message)

        return image

    async def __call__(self, image: Image) -> Image:
        """Find astrometric solution on given image.

        Writes WCSERR=1 into FITS header on failure.

        Args:
            image: Image to analyse.
        """

        try:
            return await self._process(image)
        except exc.ImageError as e:
            return self._handle_error(image, e)


__all__ = ["AstrometryDotNet"]
