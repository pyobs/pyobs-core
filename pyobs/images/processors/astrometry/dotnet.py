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
    """
    Perform astrometric solving using an astrometry.net-compatible service.

    This asynchronous processor submits sources extracted from a
    :class:`pyobs.images.Image` to an astrometry.net service, obtains a WCS solution,
    and writes it back to the image’s FITS header. The solver endpoint is configured
    via ``url`` and the request content is built by
    :class:`pyobs.images.processors.astrometry._DotNetRequestBuilder`.

    :param str url: Base URL of the astrometry.net service endpoint
                    (e.g., a local server or https://nova.astrometry.net/api).
    :param int source_count: Number of detected sources to include in the request
                             payload. The source selection strategy is defined by
                             ``_DotNetRequestBuilder``. Default: ``50``.
    :param float radius: Search radius constraint passed to the request builder.
                         Units and semantics are defined by ``_DotNetRequestBuilder``
                         (commonly degrees for astrometry.net). Default: ``3.0``.
    :param int timeout: Timeout in seconds for the network call to the astrometry
                        web service. Default: ``10``.
    :param bool exceptions: Whether to raise exceptions on failure. If ``True``,
                            processing errors are raised (typically as
                            :class:`pyobs.images.exceptions.ImageError`). If ``False``,
                            errors are handled by marking the image header and returning
                            the original image. Default: ``True``.
    :param kwargs: Additional keyword arguments forwarded to
                   :class:`pyobs.images.processors.astrometry.Astrometry`.

    Behavior
    --------
    - Constructs a request from the input image using
      :class:`pyobs.images.processors.astrometry._DotNetRequestBuilder(source_count, radius)`.
    - Logs request metadata via :class:`pyobs.images.processors.astrometry._RequestLogger`.
    - Sends the request to the configured service with ``request.send(url, timeout)``.
    - On success, receives solver output and writes the resulting WCS into a copy of
      the input image using :class:`pyobs.images.processors.astrometry._ResponseImageWriter`.
    - Logs the outcome, including WCS information, and returns the result image.
    - On failure:
      - If ``exceptions=True``, raises the underlying
        :class:`pyobs.images.exceptions.ImageError`.
      - If ``exceptions=False``, sets ``WCSERR=1`` in the FITS header, logs a warning,
        and returns the original image unchanged.

    Input/Output
    ------------
    - Input: :class:`pyobs.images.Image`
    - Output: :class:`pyobs.images.Image` (copied) with WCS solution written to the
      FITS header. Pixel data are typically unchanged.

    Configuration (YAML)
    --------------------
    Minimal local solver:

    .. code-block:: yaml

       class: pyobs.images.processors.astrometry.AstrometryDotNet
       url: "http://localhost:8080/api"

    Use the public nova service and adjust source selection and timeout:

    .. code-block:: yaml

       class: pyobs.images.processors.astrometry.AstrometryDotNet
       url: "https://nova.astrometry.net/api"
       source_count: 100
       radius: 2.0
       timeout: 30

    Handle failures without raising exceptions:

    .. code-block:: yaml

       class: pyobs.images.processors.astrometry.AstrometryDotNet
       url: "https://nova.astrometry.net/api"
       exceptions: false

    Notes
    -----
    - The ``_DotNetRequestBuilder`` determines how sources are extracted and how the
      request is formed (including any unit conventions for ``radius``). Consult its
      documentation for details.
    - If authentication or API keys are required by the service, ensure they are
      handled by the builder or included in the service configuration.
    - ``WCSERR`` is used as a failure marker in the FITS header when ``exceptions=False``.
    - This processor is asynchronous; call it within an event loop (using ``await``).

    Raises
    ------
    - :class:`pyobs.images.exceptions.ImageError`: When processing fails and
      ``exceptions=True``.
    - :class:`RuntimeError`: If the request completes without a response
      (``request.response_data is None``). Note that this specific error is not
      caught by :meth:`__call__` and will propagate unless handled externally.
    """

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
        if request.response_data is None:
            raise RuntimeError("No response")

        response_writer = _ResponseImageWriter(request.response_data, image)
        result_image = response_writer()

        logger.log_request_result(response_writer.image_wcs)

        return result_image

    def _handle_error(self, image: Image, error: exc.ImageError) -> Image:
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
