import asyncio
import threading

import pandas as pd
import logging
from concurrent.futures import ThreadPoolExecutor
import tornado.gen
import tornado.web
import tornado.ioloop

from .publisher import Publisher


log = logging.getLogger(__name__)


class MainHandler(tornado.web.RequestHandler):
    def initialize(self):
        """Initializes the handler (instead of in the constructor)"""
        self.executor = ThreadPoolExecutor(max_workers=10)

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


class HttpPublisher(Publisher, tornado.web.Application):
    def __init__(self, port: int, *args, **kwargs):
        """Initialize new CSV publisher.

        Args:
            filename: Name of file to log in.
        """
        Publisher.__init__(self, *args, **kwargs)

        # add thread func
        self._add_thread_func(self._http, False)

        # init tornado web server
        tornado.web.Application.__init__(self, [
            (r"/(.*)", MainHandler),
        ])

        # store stuff
        self._io_loop = None
        self._lock = threading.RLock()
        self._port = port

    def close(self):
        """Close server."""

        # close io loop and parent
        self._io_loop.add_callback(self._io_loop.stop)
        Publisher.close(self)

    def _http(self):
        """Thread function for the web server."""

        # create io loop
        asyncio.set_event_loop(asyncio.new_event_loop())
        self._io_loop = tornado.ioloop.IOLoop.current()
        self._io_loop.make_current()

        # start listening
        log.info('Starting HTTP server on port %d.', self._port)
        self.listen(self._port)

        # start the io loop
        self._io_loop.start()

    def __call__(self, **kwargs):
        """Publish the given results.

        Args:
            **kwargs: Results to publish.
        """

        # load data
        try:
            # load it
            csv = self.vfs.read_csv(self._filename, index_col=False)

        except FileNotFoundError:
            # file not found, so start new with row
            csv = pd.DataFrame()

        # create new row from kwargs and append it
        row = pd.DataFrame(kwargs, index=[0])
        csv = pd.concat([csv, row], ignore_index=True)

        # write it
        self.vfs.write_csv(csv, self._filename, index=False)


__all__ = ['HttpPublisher']
