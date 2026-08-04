from __future__ import annotations

import hmac
import logging
from typing import Any

import aiohttp
from aiohttp import web

from pyobs.modules import Module
from pyobs.utils.cache import DataCache

log = logging.getLogger(__name__)


class HttpFileCache(Module):
    """A file cache based on a HTTP server."""

    def __init__(
        self,
        port: int = 37075,
        cache_size: int = 25,
        max_file_size: int = 100,
        token: str | None = None,
        **kwargs: Any,
    ):
        """Initializes file cache.

        Args:
            port: Port for HTTP server.
            cache_size: Size of file cache, i.e. number of files to cache.
            max_file_size: Maximum file size in MB.
            token: Shared secret required in the "Authorization: Bearer <token>" header for
                download/upload access. If None (default), no auth is enforced.
        """
        Module.__init__(self, **kwargs)

        # store stuff
        self._cache = DataCache(cache_size)
        self._is_listening = False
        self._port = port
        self._cache_size = cache_size
        self._max_file_size = max_file_size * 1024 * 1024
        self._token = token

        # define web server
        self._app = web.Application(client_max_size=self._max_file_size)
        self._app.add_routes(
            [
                web.get("/ping", self.ping_handler),
                web.get("/{filename}", self.download_handler),
                web.options("/{filename}", self.options_handler),
                web.post("/", self.upload_handler),
            ]
        )
        self._runner = web.AppRunner(self._app)
        self._site: web.TCPSite | None = None

    async def open(self) -> None:
        """Open server"""
        await Module.open(self)

        # start listening
        log.info("Starting HTTP file cache on port %d...", self._port)
        await self._runner.setup()
        self._site = web.TCPSite(self._runner, "0.0.0.0", self._port)
        await self._site.start()
        self._is_listening = True

    async def close(self) -> None:
        """Close server"""
        await Module.close(self)

        # stop server
        await self._runner.cleanup()

    @property
    def opened(self) -> bool:
        """Whether the server is started."""
        return self._is_listening

    def _check_auth(self, request: web.Request) -> None:
        """Raises HTTPUnauthorized if a token is configured and the request doesn't carry it.

        Args:
            request: Request to check.
        """
        if self._token is None:
            return
        prefix = "Bearer "
        header = request.headers.get("Authorization", "")
        if not header.startswith(prefix) or not hmac.compare_digest(header[len(prefix) :], self._token):
            raise web.HTTPUnauthorized()

    async def ping_handler(self, request: web.Request) -> web.Response:
        """Handles GET access to /ping for testing connectivity.

        Args:
            request: Request to respond to.

        Returns:
            Response with a JSON status.
        """
        return web.json_response({"status": "ok"}, headers={"Access-Control-Allow-Origin": "*"})

    async def options_handler(self, request: web.Request) -> web.Response:
        """Handles OPTIONS access to /{filename} for CORS preflight requests.

        Args:
            request: Request to respond to.

        Returns:
            Empty response with CORS headers.
        """
        return web.Response(
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET",
                "Access-Control-Allow-Headers": "Authorization",
            }
        )

    async def download_handler(self, request: web.Request) -> web.Response:
        """Handles GET access to /{filename} and returns image.

        Args:
            request: Request to respond to.

        Returns:
            Response containing image.
        """
        self._check_auth(request)

        # get filename
        filename = request.match_info["filename"]

        # get data
        if filename not in self._cache:
            raise web.HTTPNotFound()
        data = self._cache[filename]

        # send it
        log.info("Serving file %s.", filename)
        return web.Response(body=data, headers={"Access-Control-Allow-Origin": "*"})

    async def upload_handler(self, request: web.Request) -> web.Response:
        """Handles PUSH access to /, stores image and returns filename.

        Args:
            request: Request to respond to.

        Returns:
            Response containing filename.
        """
        self._check_auth(request)

        # read multipart data
        reader = await request.multipart()
        filename: str | None = None
        data: bytes | None = None
        async for field in reader:
            # we expect a file called 'file'
            if isinstance(field, aiohttp.BodyPartReader) and field.name == "file":
                filename = field.filename
                data = await field.read()
                break

        # no filename
        if filename is None:
            raise web.HTTPNotFound()

        # store it
        log.info("Storing file %s.", filename)
        self._cache[filename] = data

        # return filename
        return web.Response(body=filename)


__all__ = ["HttpFileCache"]
