import logging
from typing import Any
from aiohttp import web

from pyobs.images.processor import ImageProcessor
from pyobs.images import Image
from .saveimage import SaveImage

log = logging.getLogger(__name__)


class HttpServer(ImageProcessor):
    """Serve image via HTTP."""

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
