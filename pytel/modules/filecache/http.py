import asyncio
import logging
import re
import threading
import uuid
from collections import namedtuple
from concurrent.futures import ThreadPoolExecutor
import time
import tornado.ioloop
import tornado.web
import tornado.gen

from pytel import PytelModule

log = logging.getLogger(__name__)


class MainHandler(tornado.web.RequestHandler):
    def initialize(self):
        self.executor = ThreadPoolExecutor(max_workers=30)

    @tornado.gen.coroutine
    def post(self, dummy):
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
    def get(self, filename):
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


CacheEntry = namedtuple('CacheEntry', 'filename data time')


class HttpFileCacheServer(PytelModule, tornado.web.Application):
    def __init__(self, port: int = 37075, path: str = None, cache_size: int = 25, *args, **kwargs):
        PytelModule.__init__(self, path=path, thread_funcs=self._http, restart_threads=False, *args, **kwargs)
        tornado.web.Application.__init__(self, [
            (r"/(.*)", MainHandler),
        ])
        self._io_loop = None
        self._cache = []
        self._lock = threading.RLock()
        self._is_listening = False
        self._port = port
        self._path = path
        self._cache_size = cache_size

    def close(self):
        #self._io_loop.stop()
        self._io_loop.add_callback(self._io_loop.stop)
        PytelModule.close(self)

    @property
    def opened(self):
        return self._is_listening

    def _http(self):
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

    def store(self, data: bytearray, filename: str = None):
        with self._lock:
            # no filename given?
            if filename is None:
                filename = str(uuid.uuid4())

            # store it
            self._cache.append(CacheEntry(filename=filename, data=data, time=time.time()))

            # too many entries?
            if len(self._cache) > self._cache_size:
                # first sort cache by time and truncate to latest X elements
                self._cache.sort(key=lambda c: c.time)
                self._cache = self._cache[-self._cache_size:]

            # finally, filename
            return filename

    def fetch(self, filename: str):
        with self._lock:
            # find file in cache and return it
            for entry in self._cache:
                if entry.filename == filename:
                    return entry.data

        # if we came here, no file has been found
        return None


__all__ = ['HttpFileCacheServer']
