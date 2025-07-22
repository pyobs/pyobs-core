import asyncio
import io
import json
import threading
from typing import Any

import pandas as pd
import logging
import tornado.gen
import tornado.web
import tornado.ioloop

from .publisher import Publisher


log = logging.getLogger(__name__)

# class LatestJsonHandler(tornado.web.RequestHandler):
#     """Latest data as JSON."""
#
#     @tornado.gen.coroutine
#     def get(self) -> None:
#         # app
#         if not isinstance(self.application, HttpPublisher):
#             return
#
#         # set header
#         self.set_header("content-type", "application/json")
#
#         # no data?
#         data = self.application.data
#         if len(data) == 0:
#             self.finish()
#             return
#
#         # convert last row to dict
#         row = data.iloc[-1].to_dict()
#
#         self.set_header("content-type", "application/json")
#         self.write(json.dumps(row))
#         self.finish()
#
#
# class HistoryCsvHandler(tornado.web.RequestHandler):
#     """History as CSV."""
#
#     @tornado.gen.coroutine
#     def get(self) -> None:
#         # app
#         if not isinstance(self.application, HttpPublisher):
#             return
#
#         # set header
#         self.set_header("content-type", "text/csv")
#
#         # write data
#         with io.StringIO() as sio:
#             self.application.data.to_csv(sio, index=False)
#             self.write(sio.getvalue())
#             self.finish()
#
#
# class HttpPublisher(Publisher, tornado.web.Application):
#     def __init__(self, port: int = 37077, keep: int = 10, **kwargs: Any):
#         """Initialize new CSV publisher.
#
#         Args:
#             filename: Name of file to log in.
#             keep: Number of entries to keep.
#         """
#         Publisher.__init__(self, **kwargs)
#
#         # add thread func
#         self.add_background_task(self._http, False)
#
#         # init tornado web server
#         tornado.web.Application.__init__(
#             self, [(r"/latest.json", LatestJsonHandler), (r"/history.csv", HistoryCsvHandler)]
#         )
#
#         # store stuff
#         self._io_loop: tornado.ioloop.IOLoop | None = None
#         self._lock = threading.RLock()
#         self._port = port
#         self._keep = keep
#         self._data = pd.DataFrame()
#
#     async def close(self) -> None:
#         """Close server."""
#
#         # close io loop and parent
#         if self._io_loop is not None:
#             self._io_loop.add_callback(self._io_loop.stop)
#         await Publisher.close(self)
#
#     @property
#     def data(self) -> pd.DataFrame:
#         with self._lock:
#             return self._data.copy()
#
#     def _http(self) -> None:
#         """Thread function for the web server."""
#
#         # create io loop
#         asyncio.set_event_loop(asyncio.new_event_loop())
#         self._io_loop = tornado.ioloop.IOLoop.current()
#         self._io_loop.make_current()
#
#         # start listening
#         log.info("Starting HTTP server on port %d.", self._port)
#         self.listen(self._port)
#
#         # start the io loop
#         self._io_loop.start()
#
#     async def __call__(self, **kwargs: Any) -> None:
#         """Publish the given results.
#
#         Args:
#             **kwargs: Results to publish.
#         """
#
#         # lock
#         with self._lock:
#             # append data
#             row = pd.DataFrame(kwargs, index=[0])
#             self._data = pd.concat([self._data, row], ignore_index=True)
#
#             # truncate
#             if len(self.data) > self._keep:
#                 self._data = self._data.iloc[-self._keep :]
#
#
# __all__ = ["HttpPublisher"]
