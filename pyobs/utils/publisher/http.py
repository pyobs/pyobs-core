import asyncio
import json
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
    def get(self, file_type: str):
        """Handle download request.

        Args:
            file_type: Type of data to return.
        """

        # get data
        data = self.application.data

        # what type?
        if file_type == 'json':
            # JSON file
            self.set_header('content-type', 'application/json')
            self.write(json.dumps(data))
            self.finish()

        elif file_type == 'csv':
            # CSV table, build header and value lines
            header = ','.join(data.keys())
            data = ','.join([str(d) for d in data.values()])

            # send to client
            self.set_header('content-type', 'text/csv')
            self.write(header + '\n' + data)
            self.finish()


class HttpPublisher(Publisher, tornado.web.Application):
    def __init__(self, port: int = 37077, *args, **kwargs):
        """Initialize new CSV publisher.

        Args:
            filename: Name of file to log in.
        """
        Publisher.__init__(self, *args, **kwargs)

        # add thread func
        self._add_thread_func(self._http, False)

        # init tornado web server
        tornado.web.Application.__init__(self, [
            (r"/data\.(.*)", MainHandler),
        ])

        # store stuff
        self._io_loop = None
        self._lock = threading.RLock()
        self._port = port
        self.data = {}

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

        # store data
        self.data = kwargs


__all__ = ['HttpPublisher']
