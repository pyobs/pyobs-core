from datetime import datetime
import io
import logging
import threading
import time
import asyncio
from typing import Dict, Any, Tuple

import numpy as np
import tornado
import tornado.web
import PIL.Image

from pyobs.modules import Module
from pyobs.interfaces import ICameraExposureTime, IWebcam
from ...images import Image
from ...mixins.imagegrabber import ImageGrabberMixin
from ...utils.cache import DataCache

log = logging.getLogger(__name__)

INDEX_HTML = """
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8">
    <title>Title</title>
  </head>
  <body>
    <img src="/video.mjpg">
  </body>
</html>

"""

class MainHandler(tornado.web.RequestHandler):
    @tornado.gen.coroutine
    def get(self):
        self.write(INDEX_HTML)


class VideoHandler(tornado.web.RequestHandler):
    @tornado.gen.coroutine
    def get(self):
        self.set_header('Cache-Control', 'no-store, no-cache, must-revalidate, pre-check=0, post-check=0, max-age=0')
        self.set_header('Pragma', 'no-cache')
        self.set_header('Content-Type', 'multipart/x-mixed-replace;boundary=--jpgboundary')
        self.set_header('Connection', 'close')

        self.served_image_timestamp = time.time()
        my_boundary = "--jpgboundary\r\n"
        last_num = None
        while True:
            try:
                # Generating images for mjpeg stream and wraps them into http resp
                num, image = self.application.image_jpeg
                if num != last_num:
                    last_num = num
                    self.write(my_boundary)
                    self.write("Content-type: image/jpeg\r\n")
                    self.write("Content-length: %s\r\n\r\n" % len(image))
                    self.write(image)
                    self.served_image_timestamp = time.time()
                    yield self.flush()
                else:
                    yield tornado.gen.sleep(0.1)
            except tornado.iostream.StreamClosedError:
                # stream closed
                break


class ImageHandler(tornado.web.RequestHandler):
    @tornado.gen.coroutine
    def get(self, filename):
        # fetch data
        data = self.application.fetch(filename)
        if data is None:
            raise tornado.web.HTTPError(404)
        log.info('Serving file %s...', filename)

        # send image
        self.set_header('Cache-Control', 'no-store, no-cache, must-revalidate, pre-check=0, post-check=0, max-age=0')
        self.set_header('Pragma', 'no-cache')
        self.set_header('Content-Type', 'image/fits')
        self.set_header("Content-length", len(data))
        self.write(data)
        self.finish()


class BaseWebcam(Module, tornado.web.Application, ImageGrabberMixin, IWebcam, ICameraExposureTime):
    """Base class for all webcam modules."""
    __module__ = 'pyobs.modules.camera'

    def __init__(self, http_port: int = 37077, interval: float = 0.5, video_path: str = '/webcam/video.mjpg',
                 filenames: str = '/webcam/pyobs-{DAY-OBS|date:}-{FRAMENUM|string:04d}.fits',
                 fits_namespaces: list = None, fits_headers: Dict[str, Any] = None, centre: Tuple[float, float] = None,
                 rotation: float = 0., cache_size: int = 5, *args, **kwargs):
        """Creates a new BaseWebcam.

        On the receiving end, a VFS root with a HTTPFile must exist with the same name as in image_path and video_path,
        i.e. "webcam" in the default settings.

        Args:
            http_port: HTTP port for webserver.
            exposure_time: Initial exposure time.
            interval: Min interval for grabbing images.
            video_path: VFS path to video.
            filename: Filename pattern for FITS images.
            fits_namespaces: List of namespaces for FITS headers that this camera should request.
            fits_headers: Additional FITS headers.
            centre: (x, y) tuple of camera centre.
            rotation: Rotation east of north.
            cache_size: Size of cache for previous images.
        """
        Module.__init__(self, *args, **kwargs)
        ImageGrabberMixin.__init__(self, fits_namespaces=fits_namespaces, fits_headers=fits_headers, centre=centre,
                                   rotation=rotation, filenames=filenames)

        # store
        self._io_loop = None
        self._lock = threading.RLock()
        self._is_listening = False
        self._port = http_port
        self._interval = interval
        self._new_image_event = threading.Event()
        self._video_path = video_path
        self._frame_num = 0

        # image cache
        self._cache = DataCache(cache_size)

        # init tornado web server
        tornado.web.Application.__init__(self, [
            (r"/", MainHandler),
            (r"/video.mjpg", VideoHandler),
            (r"/(.*)", ImageHandler),
        ])
        self._last_data = None
        self._image_jpeg = None
        self._image_time = None

        # add thread func
        self.add_thread_func(self._http, False)

    def open(self):
        """Open module."""
        Module.open(self)

    def close(self):
        """Close server."""

        # close io loop and parent
        self._io_loop.add_callback(self._io_loop.stop)
        Module.close(self)

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
        log.info('Starting HTTP server on port %d...', self._port)
        self.listen(self._port)

        # start the io loop
        self._is_listening = True
        self._io_loop.start()

    @property
    def image_jpeg(self):
        with self._lock:
            return self._frame_num, self._image_jpeg

    def _set_image(self, data: np.ndarray):
        """Create FITS and JPEG images from data."""

        # check interval
        now = time.time()
        if self._image_time is not None and now < self._image_time + self._interval:
            return
        self._image_time = now

        # write to buffer and return it
        with io.BytesIO() as output:
            PIL.Image.fromarray(data).save(output, format="jpeg")
            image_jpeg = output.getvalue()

        # store both
        with self._lock:
            self._image_time = now
            self._last_data = data
            self._image_jpeg = image_jpeg
            self._frame_num += 1

        # signal it
        self._new_image_event.set()
        self._new_image_event = threading.Event()

    def grab_image(self, broadcast: bool = True, *args, **kwargs) -> str:
        """Grabs an image ans returns reference.

        Args:
            broadcast: Broadcast existence of image.

        Returns:
            Name of image that was taken.
        """

        # we want an image that starts exposing AFTER now, so we wait for the current image to finish.
        log.info('Waiting for last image to finish...')
        self._new_image_event.wait()

        # remember time of start of exposure
        date_obs = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")

        # request fits headers
        self.request_fits_headers()

        # now we wait for the real image and grab it
        log.info('Waiting for real image to finish...')
        self._new_image_event.wait()
        image = Image(self._last_data)
        image.header['DATE-OBS'] = date_obs

        # add fits headers and format filename
        self.add_fits_headers(image)
        filename = self.format_filename(image)

        # store it and return filename
        log.info('Writing image %s to cache...', filename)
        with self._lock:
            self._cache[image.header['FNAME']] = image.to_bytes()
        return filename

    def get_video(self, *args, **kwargs) -> str:
        """Returns path to video.

        Returns:
            Path to video.
        """
        return self._video_path

    def fetch(self, filename: str) -> bytearray:
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


__all__ = ['BaseWebcam']
