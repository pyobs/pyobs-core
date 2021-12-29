import logging
from typing import Any, Optional
from aiohttp import web

from pyobs.modules import Module
from pyobs.utils.cache import DataCache

log = logging.getLogger(__name__)


class HttpFileCache(Module):
    """A file cache based on a HTTP server."""

    def __init__(self, port: int = 37075, cache_size: int = 25, max_file_size: int = 100, **kwargs: Any):
        """Initializes file cache.

        Args:
            port: Port for HTTP server.
            cache_size: Size of file cache, i.e. number of files to cache.
            max_file_size: Maximum file size in MB.
        """
        Module.__init__(self, **kwargs)

        # store stuff
        self._cache = DataCache(cache_size)
        self._is_listening = False
        self._port = port
        self._cache_size = cache_size
        self._max_file_size = max_file_size * 1024 * 1024

        # define web server
        self._app = web.Application()
        self._app.add_routes([web.get('/{filename}', self.download_handler),
                              web.post('/', self.upload_handler)])
        self._runner = web.AppRunner(self._app)
        self._site: Optional[web.TCPSite] = None

    async def open(self) -> None:
        """Open server"""
        await Module.open(self)

        # start listening
        log.info('Starting HTTP file cache on port %d...', self._port)
        await self._runner.setup()
        self._site = web.TCPSite(self._runner, '0.0.0.0', self._port)
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

    async def download_handler(self, request: web.Request) -> web.Response:
        """Handles GET access to /{filename} and returns image.

        Args:
            request: Request to respond to.

        Returns:
            Response containing image.
        """

        # get filename
        filename = request.match_info['filename']

        # get data
        if filename not in self._cache:
            raise web.HTTPNotFound()
        data = self._cache[filename]

        # send it
        log.info(f'Serving file {filename}.')
        return web.Response(body=data)

    async def upload_handler(self, request: web.Request) -> web.Response:
        """Handles PUSH access to /, stores image and returns filename.

        Args:
            request: Request to respond to.

        Returns:
            Response containing filename.
        """

        # read multipart data
        reader = await request.multipart()
        filename: Optional[str] = None
        data: Optional[bytes] = None
        async for field in reader:
            # we expect a file called 'file'
            if field.name == 'file':
                filename = field.filename
                data = await field.read()
                break

        # no filename
        if filename is None:
            raise web.HTTPNotFound()

        # store it
        log.info(f'Storing file {filename}.')
        self._cache[filename] = data

        # return filename
        return web.Response(body=filename)


__all__ = ['HttpFileCache']
