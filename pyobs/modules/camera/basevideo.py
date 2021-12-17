from abc import ABCMeta
from collections import Coroutine
from datetime import datetime
import io
import logging
import time
import asyncio
from typing import Dict, Any, Tuple, NamedTuple, Optional, List
import numpy as np
import tornado
import tornado.web
import tornado.gen
import tornado.iostream
import tornado.ioloop
import PIL.Image
from numpy.typing import NDArray

from pyobs.modules import Module, timeout
from pyobs.interfaces import IVideo, IImageType, IExposureTime
from pyobs.events import NewImageEvent
from pyobs.images import Image
from pyobs.mixins.fitsheader import ImageFitsHeaderMixin
from pyobs.utils.cache import DataCache
from pyobs.utils.enums import ImageType

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


async def calc_expose_timeout(webcam: IExposureTime, *args: Any, **kwargs: Any) -> float:
    """Calculates timeout for grabe_image()."""
    if hasattr(webcam, 'get_exposure_time'):
        return 2. * await webcam.get_exposure_time() + 30.
    else:
        return 30.


class NextImage(NamedTuple):
    date_obs: str
    image_type: ImageType
    header_futures: Dict[str, Coroutine]
    broadcast: bool


class ImageRequest:
    def __init__(self, broadcast: bool = True):
        self.broadcast: bool = broadcast
        self.image: Optional[Image] = None
        self.filename: Optional[str] = None


class LastImage(NamedTuple):
    data: NDArray[Any]
    image: Optional[Image]
    jpeg: Optional[bytes]
    filename: Optional[str]


class MainHandler(tornado.web.RequestHandler):
    async def get(self) -> None:
        self.write(INDEX_HTML)
        await self.finish()


class VideoHandler(tornado.web.RequestHandler):
    async def get(self) -> Any:
        self.application: BaseVideo
        self.set_header('Cache-Control', 'no-store, no-cache, must-revalidate, pre-check=0, post-check=0, max-age=0')
        self.set_header('Pragma', 'no-cache')
        self.set_header('Content-Type', 'multipart/x-mixed-replace;boundary=--jpgboundary')
        self.set_header('Connection', 'close')

        my_boundary = "--jpgboundary\r\n"
        last_num = None
        last_time = 0.
        while True:
            try:
                # Generating images for mjpeg stream and wraps them into http resp
                num, image = await self.application.image_jpeg()
                if image is None:
                    continue
                if num != last_num or time.time() > last_time + 10:
                    last_num = num
                    last_time = time.time()
                    self.write(my_boundary)
                    self.write("Content-type: image/jpeg\r\n")
                    self.write("Content-length: %s\r\n\r\n" % len(image))
                    self.write(image)
                    await self.flush()
                else:
                    await asyncio.sleep(0.1)
            except tornado.iostream.StreamClosedError:
                # stream closed
                break


class ImageHandler(tornado.web.RequestHandler):
    async def get(self, filename: str) -> Any:
        self.application: BaseVideo
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
        await self.finish()


class BaseVideo(Module, tornado.web.Application, ImageFitsHeaderMixin, IVideo, IImageType, metaclass=ABCMeta):
    """Base class for all webcam modules."""
    __module__ = 'pyobs.modules.camera'

    def __init__(self, http_port: int = 37077, interval: float = 0.5, video_path: str = '/webcam/video.mjpg',
                 filenames: str = '/webcam/pyobs-{DAY-OBS|date:}-{FRAMENUM|string:04d}.fits',
                 fits_namespaces: Optional[List[str]] = None, fits_headers: Optional[Dict[str, Any]] = None,
                 centre: Optional[Tuple[float, float]] = None, rotation: float = 0., cache_size: int = 5,
                 live_view: bool = True, flip: bool = False, sleep_time: int = 600, **kwargs: Any):
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
            flip: Whether to flip around Y axis.
            sleep_time: Time in s with inactivity after which the camera should go to sleep.
        """
        Module.__init__(self, **kwargs)
        ImageFitsHeaderMixin.__init__(self, fits_namespaces=fits_namespaces, fits_headers=fits_headers, centre=centre,
                                      rotation=rotation, filenames=filenames)

        # store
        self._io_loop: Optional[tornado.ioloop.IOLoop] = None
        self._is_listening = False
        self._port = http_port
        self._interval = interval
        self._new_image_event = asyncio.Event()
        self._video_path = video_path
        self._frame_num = 0
        self._live_view = live_view
        self._image_type = ImageType.OBJECT
        self._image_request_lock = asyncio.Lock()
        self._image_requests: List[ImageRequest] = []
        self._next_image: Optional[NextImage] = None
        self._last_image: Optional[LastImage] = None
        self._last_time = 0.
        self._flip = flip
        self._sleep_time = sleep_time

        # active
        self._active = False
        self._active_time = 0.
        self.add_background_task(self._active_update)

        # image cache
        self._cache = DataCache(cache_size)

        # handlers
        handlers: List[Any] = [(r"/", MainHandler), (r"/video.mjpg", VideoHandler), (r"/(.*)", ImageHandler)]
        if not live_view:
            # remove video handler
            handlers.pop(1)

        # init tornado web server
        tornado.web.Application.__init__(self, handlers)

    async def open(self) -> None:
        """Open module."""
        await Module.open(self)

        # start listening
        log.info('Starting HTTP server on port %d...', self._port)
        self.listen(self._port)
        self._is_listening = True

    @property
    def opened(self) -> bool:
        """Whether the server is started."""
        return self._is_listening

    @property
    def camera_active(self) -> bool:
        """Whether camera is currently active."""
        return self._active

    async def activate_camera(self) -> None:
        """Activate camera."""
        self._active_time = time.time()
        if not self._active:
            await self._activate_camera()
        self._active = True

    async def deactivate_camera(self) -> None:
        """Deactivate camera."""
        self._active_time = 0
        if self._active:
            await self._deactivate_camera()
        self._active = False

    async def _activate_camera(self) -> None:
        """Can be overridden by derived class to implement inactivity sleep"""
        pass

    async def _deactivate_camera(self) -> None:
        """Can be overridden by derived class to implement inactivity sleep"""
        pass

    async def _active_update(self) -> None:
        """Checking active status regularly."""
        self._active_time = time.time()
        while True:
            # go to sleep?
            if time.time() - self._active_time > self._sleep_time and self._active:
                await self.deactivate_camera()

            # wait a little for next check
            await asyncio.sleep(1)

    async def image_jpeg(self) -> Tuple[Optional[int], Optional[bytes]]:
        """Return image as jpeg."""

        # activate camera, first image will most probably be None
        await self.activate_camera()

        # return what we got
        return self._frame_num, None if self._last_image is None else self._last_image.jpeg

    @staticmethod
    def create_jpeg(data: NDArray[Any]) -> bytes:
        """Create a JPEG ge from a numpy array and return as bytes.

        Args:
            data: Numpy array to convert to JPEG.

        Returns:
            Bytes containing JPEG image.
        """

        # uint16?
        if data.dtype == np.uint16:
            # TODO: find a better way to convert to uint8
            data = (data / 256).astype(np.uint8)

        # write to jpeg
        with io.BytesIO() as output:
            PIL.Image.fromarray(data).save(output, format="jpeg")
            return output.getvalue()

    async def _set_image(self, data: NDArray[Any]) -> None:
        """Create FITS and JPEG images from data."""

        # flip image?
        if self._flip:
            data: NDArray[Any] = np.flip(data, axis=0)  # type: ignore

        # got a requested image in the queue?
        image, filename = None, None
        if self._next_image is not None:
            # create image and reset
            image, filename = await self._create_image(data, self._next_image)
            self._next_image = None
            async with self._image_request_lock:
                for req in self._image_requests:
                    req.image = image
                    req.filename = filename

        # convert to jpeg only if we need live view
        now = time.time()
        jpeg = None
        if self._live_view:
            # check interval
            if now - self._last_time > self._interval:
                # write to buffer and reset interval
                loop = asyncio.get_running_loop()
                jpeg = await loop.run_in_executor(None, self.create_jpeg, data)
                self._last_time = now

        # store both
        self._last_image = LastImage(data=data, image=image, jpeg=jpeg, filename=filename)
        self._frame_num += 1

        # signal it
        self._new_image_event.set()
        self._new_image_event = asyncio.Event()

        # prepare next image
        if len(self._image_requests) > 0:
            # broadcast?
            broadcast = any([req.broadcast for req in self._image_requests])

            # store everything
            logging.info('Preparing to catch next image...')
            self._next_image = NextImage(date_obs=datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f"),
                                         image_type=self._image_type,
                                         header_futures=await self.request_fits_headers(),
                                         broadcast=broadcast)

            # reset
            self._image_request = None

    async def _create_image(self, data: NDArray[Any], next_image: NextImage) -> Tuple[Image, str]:
        """Create an Image object from numpy array.

        Args:
            data: Numpy array to convert to Image.

        Returns:
            Tuple with image itself and the filename.
        """

        # create image
        flipped: NDArray[Any] = np.flip(data, axis=0)  # type: ignore
        image = Image(flipped)
        image.header['DATE-OBS'] = next_image.date_obs
        image.header['IMAGETYP'] = next_image.image_type.value

        # add fits headers and format filename
        await self.add_requested_fits_headers(image, next_image.header_futures)
        await self.add_fits_headers(image)

        # finish it up
        return await self._finish_image(image, next_image.broadcast, next_image.image_type)

    async def _finish_image(self, image: Image, broadcast: bool, image_type: ImageType) -> Tuple[Image, str]:
        """Finish up an image at the end of _create_image.

        Args:
            image: Image to finish up.
            broadcast: Whether to broadcast it.
            image_type: Type of image.

        Returns:
            Tuple with image itself and the filename.
        """

        # format filename
        filename = self.format_filename(image)

        # store it and return filename
        log.info('Writing image %s to cache...', filename)
        self._cache[image.header['FNAME']] = image.to_bytes()

        # broadcast image path
        if broadcast and self.comm:
            log.info('Broadcasting image ID...')
            await self.comm.send_event(NewImageEvent(filename, image_type))

        # finished
        return image, filename

    @timeout(calc_expose_timeout)
    async def grab_image(self, broadcast: bool = True, **kwargs: Any) -> str:
        """Grabs an image ans returns reference.

        Args:
            broadcast: Broadcast existence of image.

        Returns:
            Name of image that was taken.
        """

        # activate camera
        await self.activate_camera()

        # acquire lock
        async with self._image_request_lock:
            # request new image
            image_request = ImageRequest(broadcast)
            self._image_requests.append(image_request)

        # we want an image that starts exposing AFTER now, so we wait for the current image to finish.
        log.info('Waiting for image to finish...')
        while image_request.image is None:
            await asyncio.sleep(0.1)

        # remove from list
        self._image_requests.remove(image_request)

        # no image?
        if image_request.image is None or image_request.filename is None:
            raise ValueError('Could not take image.')

        # finished
        return image_request.filename

    async def get_video(self, **kwargs: Any) -> str:
        """Returns path to video.

        Returns:
            Path to video.
        """
        return self._video_path

    def fetch(self, filename: str) -> Optional[bytearray]:
        """Send a file to the requesting client.

        Args:
            filename: Name of file to send.

        Returns:
            Data of file.
        """

        # find file in cache and return it
        return self._cache[filename] if filename in self._cache else None

    async def set_image_type(self, image_type: ImageType, **kwargs: Any) -> None:
        """Set the image type.

        Args:
            image_type: New image type.
        """
        log.info('Setting image type to %s...', image_type)
        self._image_type = image_type

    async def get_image_type(self, **kwargs: Any) -> ImageType:
        """Returns the current image type.

        Returns:
            Current image type.
        """
        return self._image_type


__all__ = ['BaseVideo']
