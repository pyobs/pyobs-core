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

    This processor submits sources extracted from a
    :class:`pyobs.images.Image` to an astrometry.net service, obtains a WCS solution,
    and writes it back to the image’s FITS header. The solver endpoint is configured
    via ``url`` and the request content is built by
    :class:`pyobs.images.processors.astrometry._DotNetRequestBuilder`.

    :param str url: Base URL of the astrometry.net service endpoint.
    :param int source_count: Number of detected sources to include in the request
                             payload. The source selection strategy is defined by
                             ``_DotNetRequestBuilder``. Default: ``50``.
    :param float radius: Search radius constraint passed to the request builder.
                         Units and semantics are defined by ``_DotNetRequestBuilder``
                         (commonly degrees for astrometry.net). Default: ``3.0``.
    :param int timeout: Timeout in seconds for the network call to the astrometry
                        web service. Default: ``10``.
    :param bool exceptions: Deprecated, use ``on_error`` instead. ``exceptions=False`` is
                            equivalent to ``on_error="error"``; ``exceptions=True`` (the
                            default) is equivalent to ``on_error="raise"``.
    :param str on_error: How the pipeline should handle a failed solve: ``"raise"`` (default,
                         abort the pipeline), ``"error"`` (mark ``WCSERR=1`` in the header, log
                         a warning, and pass the image through -- see ``handle_error``),
                         ``"info"``, or ``"ignore"``. Only takes effect when this processor
                         runs as a step in a ``PipelineMixin`` pipeline; a direct call always
                         raises on failure.
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
    - On failure, raises the underlying :class:`pyobs.images.exceptions.ImageError`. When run as
      a pipeline step with ``on_error="error"``, the pipeline calls ``handle_error``, which sets
      ``WCSERR=1`` in the FITS header, logs a warning, and returns the original image unchanged.

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

    Handle failures without aborting the pipeline:

    .. code-block:: yaml

       class: pyobs.images.processors.astrometry.AstrometryDotNet
       url: "http://localhost:8080/api"
       on_error: error

    Notes
    -----
    - The ``_DotNetRequestBuilder`` determines how sources are extracted and how the
      request is formed (including any unit conventions for ``radius``). Consult its
      documentation for details.
    - ``WCSERR`` is used as a failure marker in the FITS header when ``handle_error`` runs.
    """

    __module__ = "pyobs.images.processors.astrometry"

    def __init__(
        self,
        url: str,
        source_count: int = 50,
        radius: float = 3.0,
        timeout: int = 10,
        exceptions: bool | None = None,
        on_error: str = "raise",
        **kwargs: Any,
    ):
        """Init new astronomy.net processor.

        Args:
            url: URL to service.
            source_count: Number of sources to send.
            radius: Radius to search in.
            timeout: Timeout in seconds for call to astrometry web service.
            exceptions: Deprecated, use on_error instead. Whether to raise Exceptions.
            on_error: How to handle a failed solve. One of "raise", "error", "info", "ignore".
                On "error", handle_error() marks the image with WCSERR=1 and logs a warning.
        """
        Astrometry.__init__(self, on_error=on_error, **kwargs)

        self.url = url

        self.timeout = timeout

        # backwards compat: if 'exceptions' is set but 'on_error' is left at its default,
        # derive on_error from it.
        if exceptions is not None and on_error == "raise":
            self._on_error = "raise" if exceptions else "error"

        self._request_builder = _DotNetRequestBuilder(source_count, radius)

    @property
    def exceptions(self) -> bool:
        """Deprecated, use on_error instead."""
        return self.on_error != "error"

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

    def handle_error(self, image: Image, error: exc.ImageError) -> Image:
        image.header["WCSERR"] = 1

        log.warning(error.message)

        return image

    async def __call__(self, image: Image) -> Image:
        """Find astrometric solution on given image.

        Writes WCSERR=1 into FITS header on failure (see handle_error).

        Args:
            image: Image to analyse.
        """

        return await self._process(image)


__all__ = ["AstrometryDotNet"]
