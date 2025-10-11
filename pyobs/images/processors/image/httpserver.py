import logging
from typing import Any
from aiohttp import web

from pyobs.images.processor import ImageProcessor
from pyobs.images import Image
from .saveimage import SaveImage

log = logging.getLogger(__name__)


class HttpServer(ImageProcessor):
    """
    Serve the latest processed image via a minimal HTTP server.

    This asynchronous processor starts an :mod:`aiohttp` web server on first invocation and
    serves the most recently processed image at two endpoints:

    - ``GET /``: A simple HTML page embedding the image.
    - ``GET /<filename>``: The raw encoded image bytes.

    Images are encoded using :func:`pyobs.images.processors.image.saveimage.SaveImage.encode_image`
    based on the configured ``filename`` extension or an explicitly provided ``format``.

    :param str filename: The filename to serve the image as, which also determines the path
                         (e.g., ``"image.jpg"`` served at ``/image.jpg``) and, if ``format`` is not
                         given, the encoding derived from its extension. Default: ``"image.jpg"``.
    :param str format: Explicit image format to use for encoding (e.g., ``"jpeg"``, ``"png"``,
                       ``"tiff"``). If ``None``, the format is inferred from ``filename``.
                       Default: ``None``.
    :param str url: Host/interface to bind the HTTP server to (e.g., ``"localhost"`` or
                    ``"0.0.0.0"``). Default: ``"localhost"``.
    :param int port: TCP port to serve on. Default: ``9400``.
    :param kwargs: Additional keyword arguments forwarded to
                   :class:`pyobs.images.processor.ImageProcessor`.

    :class:`pyobs.images.Image`
        The original image, unmodified.

    Behavior
    --------
    - On the first call, starts an :class:`aiohttp.web.TCPSite` bound to ``url:port`` and
      registers two routes:
      - ``GET /<filename>`` returns the currently stored image bytes with content type ``image/*``.
      - ``GET /`` returns a minimal HTML page embedding the image via ``<img src="<filename>">``.
    - Encodes the input image using
      :func:`pyobs.images.processors.image.saveimage.SaveImage.encode_image(image, filename, format)`
      and stores it as the "current" image to be served by the endpoints.
    - Subsequent calls update the stored image; clients fetching ``/<filename>`` will receive
      the latest version.
    - If no image has been processed yet, ``GET /<filename>`` responds with 404 Not Found.

    Input/Output
    ------------
    - Input: :class:`pyobs.images.Image`
    - Output: :class:`pyobs.images.Image` (unchanged), while the encoded bytes are exposed via HTTP.

    Configuration (YAML)
    --------------------
    Serve a JPEG on localhost:

    .. code-block:: yaml

       class: pyobs.images.processors.misc.HttpServer
       filename: "image.jpg"
       url: "localhost"
       port: 9400

    Serve a PNG on all interfaces:

    .. code-block:: yaml

       class: pyobs.images.processors.misc.HttpServer
       filename: "latest.png"
       url: "0.0.0.0"
       port: 8080

    Explicitly set the format (overrides filename extension):

    .. code-block:: yaml

       class: pyobs.images.processors.misc.HttpServer
       filename: "image.out"
       format: "png"

    Notes
    -----
    - This processor is asynchronous; it should be used within an event loop (``await``).
    - Binding to ``"localhost"`` exposes the server only on the local machine. Use ``"0.0.0.0"``
      to accept external connections, but be mindful of security implications.
    - No authentication or TLS is implemented; do not expose this endpoint on untrusted networks
      without additional protection.
    - The response content type is ``image/*``; some clients may expect a specific MIME type
      if the chosen format is known (e.g., ``image/jpeg`` or ``image/png``).
    - If the encoding fails (e.g., due to unsupported format), the underlying encoder may raise
      an exception; those propagate from :func:`SaveImage.encode_image`.
    """

    __module__ = "pyobs.images.processors.misc"

    def __init__(
        self,
        filename: str = "image.jpg",
        format: str | None = None,
        url: str = "localhost",
        port: int = 9400,
        **kwargs: Any,
    ):
        """Init an image processor that serves an image as jpeg, png, or whatever.

        Args:
            filename: Filename to server image as.
            format: Explicitly set the image format to use.
            url: URL to serve on.
            port: Port to serve on.
        """
        ImageProcessor.__init__(self, **kwargs)

        self._filename = filename
        self._image_format = format
        self._url = url
        self._port = port

        self._app = web.Application()
        self._app.router.add_route("GET", f"/{filename}", self._image_handler)
        self._app.router.add_route("GET", "/", self._page_handler)

        self._current_image: bytes | None = None

    async def __call__(self, image: Image) -> Image:
        """Serve image.

        Args:
            image: Image to serve.

        Returns:
            Original image.
        """

        # start http server on first image
        if self._current_image is None:
            runner = web.AppRunner(self._app)
            await runner.setup()
            site = web.TCPSite(runner, self._url, self._port)
            await site.start()

        # get image data
        self._current_image = SaveImage.encode_image(image, self._filename, self._image_format)

        return image

    async def _image_handler(self, _: web.Request) -> web.Response:
        if self._current_image is None:
            return web.HTTPNotFound()

        return web.Response(body=self._current_image, content_type="image/*")

    async def _page_handler(self, _: web.Request) -> web.Response:
        return web.Response(body=f'<html><img src="{self._filename}"></html>', content_type="text/html")


__all__ = ["HttpServer"]
