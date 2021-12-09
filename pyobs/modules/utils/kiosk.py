import asyncio
import io
import logging
from typing import Union, Any, cast, Optional
import tornado.ioloop
import tornado.web
import tornado.gen
import numpy as np

from pyobs.interfaces import ICamera, IExposureTime, IWindow
from pyobs.modules import Module
from pyobs.interfaces import IStartStop

log = logging.getLogger(__name__)


class MainHandler(tornado.web.RequestHandler):
    """The request handler for the HTTP filecache."""

    def initialize(self) -> None:
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

    async def get(self) -> Any:
        """Handle download request."""

        # get image
        app = cast(Kiosk, self.application)
        image = app.image()

        # none?
        if image is None:
            image = self._empty

        # set headers and send data
        self.set_header('content-type', 'image/jpeg')
        self.write(image)
        await self.finish()


class Kiosk(Module, tornado.web.Application, IStartStop):
    """A kiosk mode for a pyobs camera that takes images and published them via HTTP."""
    __module__ = 'pyobs.modules.utils'

    def __init__(self, camera: Union[ICamera, str], port: int = 37077, **kwargs: Any):
        """Initializes file cache.

        Args:
            camera: Camera to use for kiosk mode.
            port: Port for HTTP server.
        """
        Module.__init__(self, **kwargs)

        # add thread funcs
        self.add_background_task(self._camera_thread)

        # init tornado web server
        tornado.web.Application.__init__(self, [
            (r"/image.jpg", MainHandler),
        ])

        # store stuff
        self._io_loop: Optional[tornado.ioloop.IOLoop] = None
        self._is_listening = False
        self._camera = camera
        self._port = port
        self._exp_time = 2
        self._running = False
        self._image: Optional[bytes] = None

    async def open(self) -> None:
        """Open module."""
        await Module.open(self)

        # start listening
        log.info('Starting HTTP file cache on port %d...', self._port)
        self.listen(self._port)
        self._is_listening = True

    @property
    def opened(self) -> bool:
        """Whether the server is started."""
        return self._is_listening

    def start(self, **kwargs: Any) -> None:
        """Start kiosk mode."""
        self._running = True

    def stop(self, **kwargs: Any) -> None:
        """Stop kiosk mode."""
        self._running = False

    def is_running(self, **kwargs: Any) -> bool:
        """Whether kiosk mode is running."""
        return self._running

    async def _camera_thread(self) -> None:
        """Thread for taking images."""

        # loop until closing
        while not self.closing.is_set():
            # are we running?
            if not self._running:
                # no, so wait a little and continue
                await asyncio.sleep(1)
                continue

            # get camera
            try:
                camera: ICamera = self.proxy(self._camera, ICamera)
            except ValueError:
                await asyncio.sleep(10)
                continue

            # do settings
            if isinstance(camera, IExposureTime):
                # set exposure time
                await camera.set_exposure_time(self._exp_time)
            if isinstance(camera, IWindow):
                # set full frame
                full_frame = await camera.get_full_frame()
                await camera.set_window(*full_frame)

            # do exposure
            filename = await camera.grab_image(False)

            # download image
            try:
                image = await self.vfs.read_image(filename)
            except FileNotFoundError:
                continue

            # convert it to JPEG
            self._image = await asyncio.get_running_loop().run_in_executor(None, image.to_jpeg)

            # adjust exposure time?
            if isinstance(camera, IExposureTime):
                # get max value in image
                max_val = np.max(image.data)

                # adjust
                self._exp_time = self._exp_time / max_val * 40000

                # cut
                self._exp_time = max(self._exp_time, 30)

    def image(self) -> Optional[bytes]:
        """Return image data."""
        return self._image


__all__ = ['Kiosk']
