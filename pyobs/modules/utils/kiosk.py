import asyncio
import io
import logging
import threading
from typing import Union
import tornado.ioloop
import tornado.web
import tornado.gen
import numpy as np

from pyobs.modules import Module
from pyobs.interfaces import ICamera, ICameraExposureTime, IStoppable, ICameraWindow

log = logging.getLogger(__name__)


class MainHandler(tornado.web.RequestHandler):
    """The request handler for the HTTP filecache."""

    def initialize(self):
        """Initializes the handler (instead of in the constructor)"""

        # create empty image
        from PIL import Image, ImageDraw
        img = Image.new('RGB', (300, 300), color=(0, 0, 0))
        d = ImageDraw.Draw(img)
        d.text((110, 150), "No image taken yet", fill=(255, 255, 255))

        # create image from data array
        with io.BytesIO() as bio:
            img.save(bio, format='jpeg')
            self._empty = bio.getvalue()

    @tornado.gen.coroutine
    def get(self):
        """Handle download request."""

        # get image
        image = self.application.image()

        # none?
        if image is None:
            image = self._empty

        # set headers and send data
        self.set_header('content-type', 'image/jpeg')
        self.write(image)
        self.finish()


class Kiosk(Module, tornado.web.Application, IStoppable):
    """A kiosk mode for a pyobs camera that takes images and published them via HTTP."""

    def __init__(self, camera: Union[ICamera, str], port: int = 37077, *args, **kwargs):
        """Initializes file cache.

        Args:
            camera: Camera to use for kiosk mode.
            port: Port for HTTP server.
        """
        Module.__init__(self, *args, **kwargs)

        # add thread funcs
        self._add_thread_func(self._http_thread)
        self._add_thread_func(self._camera_thread)

        # init tornado web server
        tornado.web.Application.__init__(self, [
            (r"/image.jpg", MainHandler),
        ])

        # store stuff
        self._io_loop = None
        self._lock = threading.RLock()
        self._is_listening = False
        self._camera = camera
        self._port = port
        self._exp_time = 2
        self._running = False
        self._image = None

    def close(self):
        """Close server."""

        # close io loop and parent
        self._io_loop.add_callback(self._io_loop.stop)
        Module.close(self)

    @property
    def opened(self) -> bool:
        """Whether the server is started."""
        return self._is_listening

    def start(self, *args, **kwargs):
        """Start kiosk mode."""
        self._running = True

    def stop(self, *args, **kwargs):
        """Stop kiosk mode."""
        self._running = False

    def is_running(self, *args, **kwargs) -> bool:
        """Whether kiosk mode is running."""
        return self._running

    def _http_thread(self):
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

    def _camera_thread(self):
        """Thread for taking images."""

        # loop until closing
        while not self.closing.is_set():
            # are we running?
            if not self._running:
                # no, so wait a little and continue
                self.closing.wait(1)
                continue

            # get camera
            try:
                camera: ICamera = self.proxy(self._camera, ICamera)
            except ValueError:
                self.closing.wait(10)
                continue

            # do settings
            if isinstance(camera, ICameraExposureTime):
                # set exposure time
                camera.set_exposure_time(self._exp_time).wait()
            if isinstance(camera, ICameraWindow):
                # set full frame
                full_frame = camera.get_full_frame().wait()
                camera.set_window(*full_frame).wait()

            # do exposure
            filename = camera.expose(False).wait()

            # download image
            try:
                image = self.vfs.read_image(filename)
            except FileNotFoundError:
                continue

            # convert it to JPEG
            with self._lock:
                self._image = image.to_jpeg()

            # adjust exposure time?
            if isinstance(camera, ICameraExposureTime):
                # get max value in image
                max_val = np.max(image.data)

                # adjust
                self._exp_time = self._exp_time / max_val * 40000

                # cut
                self._exp_time = max(self._exp_time, 30)

    def image(self):
        """Return image data."""
        with self._lock:
            return self._image


__all__ = ['Kiosk']
