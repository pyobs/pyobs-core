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

from pyobs.modules import Module, timeout
from pyobs.interfaces import IVideo, IImageType
from ...events import NewImageEvent
from ...images import Image
from ...mixins.imagegrabber import ImageGrabberMixin
from ...utils.cache import DataCache
from ...utils.enums import ImageType

log = logging.getLogger(__name__)

INDEX_HTML = """
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8">
    <title>Title</title>
  </head>
  <body>
    <img src="/video.mjpg" width="100%">
  </body>
</html>

"""


def calc_expose_timeout(webcam, *args, **kwargs):
    """Calculates timeout for grabe_image()."""
    if hasattr(webcam, 'get_exposure_time'):
        return 2 * webcam.get_exposure_time() + 30
    else:
        return 30


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

        my_boundary = "--jpgboundary\r\n"
        last_num = None
        last_time = time.time()
        while True:
            try:
                # Generating images for mjpeg stream and wraps them into http resp
                num, image = self.application.image_jpeg
                if image is None:
                    continue
                if num != last_num or time.time() > last_time + 1:
                    last_num = num
                    last_time = time.time()
                    self.write(my_boundary)
                    self.write("Content-type: image/jpeg\r\n")
                    self.write("Content-length: %s\r\n\r\n" % len(image))
                    self.write(image)
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


class BaseVideo(Module, tornado.web.Application, ImageGrabberMixin, IVideo, IImageType):
    """Base class for all webcam modules."""
    __module__ = 'pyobs.modules.camera'

    def __init__(self, http_port: int = 37077, interval: float = 0.5, video_path: str = '/webcam/video.mjpg',
                 filenames: str = '/webcam/pyobs-{DAY-OBS|date:}-{FRAMENUM|string:04d}.fits',
                 fits_namespaces: list = None, fits_headers: Dict[str, Any] = None, centre: Tuple[float, float] = None,
                 rotation: float = 0., cache_size: int = 5, live_view: bool = True, *args, **kwargs):
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
            live_view: If True, live view is served via web server.
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
        self._live_view = live_view
        self._image_type = ImageType.OBJECT

        # image cache
        self._cache = DataCache(cache_size)

        # handlers
        handlers = [(r"/", MainHandler), (r"/video.mjpg", VideoHandler), (r"/(.*)", ImageHandler)]
        if not live_view:
            # remove video handler
            handlers.pop(1)

        # init tornado web server
        tornado.web.Application.__init__(self, handlers)
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

    def create_jpeg(self, data: np.ndarray) -> bytes:
        """Create a JPEG ge from a numpy array and return as bytes.

        Args:
            data: Numpy array to convert to JPEG.

        Returns:
            Bytes containing JPEG image.
        """
        with io.BytesIO() as output:
            PIL.Image.fromarray(data).save(output, format="jpeg")
            return output.getvalue()

    def _set_image(self, data: np.ndarray):
        """Create FITS and JPEG images from data."""

        # store now
        now = time.time()

        # convert to jpeg only if we need live view
        image_jpeg = None
        if self._live_view:
            # check interval
            if self._image_time is None or now - self._image_time > self._interval:
                # write to buffer and reset interval
                image_jpeg = self.create_jpeg(data)
                self._image_time = now

        # store both
        with self._lock:
            self._last_data = data
            self._image_jpeg = image_jpeg
            self._frame_num += 1

        # signal it
        self._new_image_event.set()
        self._new_image_event = threading.Event()

    def create_image(self, data: np.ndarray, date_obs: str, image_type: ImageType) -> Image:
        """Create an Image object from numpy array.

        Args:
            data: Numpy array to convert to Image.
            date_obs: DATE-OBS for this image.
            image_type: Image type of image.

        Returns:
            The image.
        """

        # create image
        image = Image(data)
        image.header['DATE-OBS'] = date_obs
        image.header['IMAGETYP'] = image_type.value

        # add fits headers and format filename
        self.add_fits_headers(image)

        # finished
        return image

    @timeout(calc_expose_timeout)
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
        image_type = self._image_type

        # request fits headers
        self.request_fits_headers()

        # now we wait for the real image and grab it
        log.info('Waiting for real image to finish...')
        self._new_image_event.wait()
        image = self.create_image(np.flip(self._last_data, 0), date_obs, image_type)

        # format filename
        filename = self.format_filename(image)

        # store it and return filename
        log.info('Writing image %s to cache...', filename)
        with self._lock:
            self._cache[image.header['FNAME']] = image.to_bytes()

        # broadcast image path
        if broadcast and self.comm:
            log.info('Broadcasting image ID...')
            self.comm.send_event(NewImageEvent(filename, ImageType.OBJECT))

        # finished
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

    def set_image_type(self, image_type: ImageType, *args, **kwargs):
        """Set the image type.

        Args:
            image_type: New image type.
        """
        log.info('Setting image type to %s...', image_type)
        self._image_type = image_type

    def get_image_type(self, *args, **kwargs) -> ImageType:
        """Returns the current image type.

        Returns:
            Current image type.
        """
        return self._image_type

__all__ = ['BaseVideo']
