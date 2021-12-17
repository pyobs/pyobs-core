import asyncio
import io
import logging
from typing import Union, Any, Optional
import numpy as np
from aiohttp import web

from pyobs.interfaces import ICamera, IExposureTime, IWindow
from pyobs.modules import Module
from pyobs.interfaces import IStartStop

log = logging.getLogger(__name__)


class Kiosk(Module, IStartStop):
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

        # store stuff
        self._is_listening = False
        self._camera = camera
        self._port = port
        self._exp_time = 2
        self._running = False
        self._image: Optional[bytes] = None

        # create empty image
        from PIL import Image, ImageDraw
        img = Image.new('RGB', (300, 300), color=(0, 0, 0))
        d = ImageDraw.Draw(img)
        d.text((110, 150), "No image taken yet", fill=(255, 255, 255))

        # create image from data array
        with io.BytesIO() as bio:
            img.save(bio, format='jpeg')
            self._empty = bio.getvalue()

        # define web server
        self._app = web.Application()
        self._app.add_routes([web.get('/image.jpg', self.image_handler)])
        self._runner = web.AppRunner(self._app)
        self._site: Optional[web.TCPSite] = None

    async def open(self) -> None:
        """Open server"""
        await Module.open(self)

        # start listening
        log.info('Starting HTTP server on port %d...', self._port)
        await self._runner.setup()
        self._site = web.TCPSite(self._runner, 'localhost', self._port)
        await self._site.start()
        self._is_listening = True

    async def close(self) -> None:
        """Close server"""
        await Module.close(self)

        # stop server
        await self._runner.cleanup()

    async def image_handler(self, request: web.Request) -> web.Response:
        """Handles access to /* and returns a specified image.

        Args:
            request: Request to respond to.

        Returns:
            Response containing image.
        """

        # get image
        image = self._empty if self._image is None else self._image

        # send it
        return web.Response(body=image, content_type='image/fits')

    @property
    def opened(self) -> bool:
        """Whether the server is started."""
        return self._is_listening

    async def start(self, **kwargs: Any) -> None:
        """Start kiosk mode."""
        self._running = True

    async def stop(self, **kwargs: Any) -> None:
        """Stop kiosk mode."""
        self._running = False

    async def is_running(self, **kwargs: Any) -> bool:
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
                camera = await self.proxy(self._camera, ICamera)
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


__all__ = ['Kiosk']
