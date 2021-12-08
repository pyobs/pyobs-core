import asyncio
import logging
import re
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Union, Any, Optional, cast
import tornado.ioloop
import tornado.web
import tornado.gen

from pyobs.modules import Module
from pyobs.utils.cache import DataCache

log = logging.getLogger(__name__)


class MainHandler(tornado.web.RequestHandler):
    """The request handler for the HTTP filecache."""
    __module__ = 'pyobs.modules.utils'

    async def post(self, dummy: str) -> Any:
        """Handle incoming file.

        Args:
            dummy: Name of incoming file.
        """

        # get app
        app = cast(HttpFileCache, self.application)

        # try to find a filename
        filename = None

        # do we have a filename in the URL?
        if dummy is not None and len(dummy) > 0:
            filename = dummy

        # do we have a content-disposition?
        elif 'Content-Disposition' in self.request.headers:
            # extract it
            m = re.search('filename="(.*)"', self.request.headers['Content-Disposition'])
            if m:
                filename = m.group(1)

        # still nothing?
        if filename is None:
            log.info('Received un-named file.')
            raise tornado.web.HTTPError(404)

        else:
            # store file and return filename
            loop = asyncio.get_running_loop()
            filename = await loop.run_in_executor(None, app.store, self.request.body, filename)
            if filename is None:
                raise tornado.web.HTTPError(404)
            log.info('Stored file as %s with %d bytes.', filename, len(self.request.body))
            await self.finish(bytes(filename, 'utf-8'))

    async def get(self, filename: str) -> Any:
        """Handle download request.

        Args:
            filename: Name of file to download.
        """

        # get app
        app = cast(HttpFileCache, self.application)

        # fetch data
        loop = asyncio.get_running_loop()
        data = await loop.run_in_executor(None, app.fetch, filename)
        if data is None:
            raise tornado.web.HTTPError(404)
        log.info('Serving file %s...', filename)

        # set headers and send data
        self.set_header('content-type', 'application/octet-stream')
        self.set_header('content-disposition', 'attachment; filename="%s"' % filename)
        self.write(data)
        await self.finish()


class HttpFileCache(Module, tornado.web.Application):
    """A file cache based on a HTTP server."""

    def __init__(self, port: int = 37075, cache_size: int = 25, max_file_size: int = 100, **kwargs: Any):
        """Initializes file cache.

        Args:
            port: Port for HTTP server.
            cache_size: Size of file cache, i.e. number of files to cache.
            max_file_size: Maximum file size in MB.
        """
        Module.__init__(self, **kwargs)

        # init tornado web server
        tornado.web.Application.__init__(self, [
            (r"/(.*)", MainHandler),
        ])

        # store stuff
        self._io_loop: Optional[tornado.ioloop.IOLoop] = None
        self._cache = DataCache(cache_size)
        self._is_listening = False
        self._port = port
        self._cache_size = cache_size
        self._max_file_size = max_file_size * 1024 * 1024

    async def open(self) -> None:
        """Open server"""

        # start listening
        log.info('Starting HTTP file cache on port %d...', self._port)
        self.listen(self._port, max_buffer_size=self._max_file_size, max_body_size=self._max_file_size)
        self._is_listening = True

    @property
    def opened(self) -> bool:
        """Whether the server is started."""
        return self._is_listening

    def store(self, data: bytearray, filename: Optional[str] = None) -> str:
        """Store an incoming file.

        Args:
            data: Data to store.
            filename: Filename to store as.

        Returns:
            Filename in cache.
        """

        # no filename given?
        if filename is None:
            # create a unique filename
            filename = str(uuid.uuid4())

        # store it
        self._cache[filename] = data

        # finally, filename
        return filename

    def fetch(self, filename: str) -> Union[None, bytearray]:
        """Send a file to the requesting client.

        Args:
            filename: Name of file to send.

        Returns:
            Data of file.
        """

        # find file in cache and return it
        return self._cache[filename] if filename in self._cache else None


__all__ = ['HttpFileCache']
