import asyncio
import logging
import re
import threading
import uuid
from collections import namedtuple
from concurrent.futures import ThreadPoolExecutor
import time
from typing import Union
import tornado.ioloop
import tornado.web
import tornado.gen

from pytel import PytelModule
from pytel.utils.cache import DataCache

log = logging.getLogger(__name__)


class MainHandler(tornado.web.RequestHandler):
    """The request handler for the HTTP filecache."""

    def initialize(self):
        """Initializes the handler (instead of in the constructor)"""

        # create a thread pool executor
        self.executor = ThreadPoolExecutor(max_workers=30)

    @tornado.gen.coroutine
    def post(self, dummy: str):
        """Handle incoming file.

        Args:
            dummy: Name of incoming file.
        """

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
            filename = yield self.executor.submit(self.application.store, self.request.body, filename)
            log.info('Stored file as %s with %d bytes.', filename, len(self.request.body))
            self.finish(bytes(filename, 'utf-8'))

    @tornado.gen.coroutine
    def get(self, filename: str):
        """Handle download request.

        Args:
            filename: Name of file to download.
        """

        # fetch data
        data = yield self.executor.submit(self.application.fetch, filename)
        if data is None:
            raise tornado.web.HTTPError(404)
        log.info('Serving file %s...', filename)

        # set headers and send data
        self.set_header('content-type', 'application/octet-stream')
        self.set_header('content-disposition', 'attachment; filename="%s"' % filename)
        self.write(data)
        self.finish()


class HttpFileCacheServer(PytelModule, tornado.web.Application):
    """A file cache based on a HTTP server."""

    def __init__(self, port: int = 37075, cache_size: int = 25, *args, **kwargs):
        """Initializes file cache.

        Args:
            port: Port for HTTP server.
            cache_size: Size of file cache, i.e. number of files to cache.
        """
        PytelModule.__init__(self, thread_funcs=self._http, restart_threads=False, *args, **kwargs)

        # init tornado web server
        tornado.web.Application.__init__(self, [
            (r"/(.*)", MainHandler),
        ])

        # store stuff
        self._io_loop = None
        self._cache = DataCache(cache_size)
        self._lock = threading.RLock()
        self._is_listening = False
        self._port = port
        self._cache_size = cache_size

    def close(self):
        """Close server."""

        # close io loop and parent
        self._io_loop.add_callback(self._io_loop.stop)
        PytelModule.close(self)

    @property
    def opened(self) -> bool:
        """Whether the server is started."""
        return self._is_listening

    def _http(self):
        """Thread function for the web server."""

        # create io loop
        asyncio.set_event_loop(asyncio.new_event_loop())
        self._io_loop = tornado.ioloop.IOLoop.current()
        self._io_loop.make_current()

        # start listening
        log.info('Starting HTTP file cache on port %d...', self._port)
        self.listen(self._port)

        # start the io loop
        self._is_listening = True
        self._io_loop.start()

    def store(self, data: bytearray, filename: str = None) -> str:
        """Store an incoming file.

        Args:
            data: Data to store.
            filename: Filename to store as.

        Returns:
            Filename in cache.
        """

        # acquire lock on cache
        with self._lock:
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

        # acquire lock on cache
        with self._lock:
            # find file in cache and return it
            return self._cache[filename] if filename in self._cache else None


__all__ = ['HttpFileCacheServer']
