import asyncio
import hashlib
import hmac
import io
import json
import logging
import time
from abc import ABCMeta
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, NamedTuple

import aiohttp
import numpy as np
import PIL.Image
from aiohttp import web
from numpy.typing import NDArray

from pyobs.events import NewImageEvent
from pyobs.images import Image
from pyobs.interfaces import IExposureTime, IImageType, ImageTypeState, IVideo, VideoCapabilities
from pyobs.mixins.fitsheader import ImageFitsHeaderMixin
from pyobs.modules import Module, timeout
from pyobs.utils import exceptions as exc
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
    <img src="video.mjpg" width="100%">
  </body>
</html>

"""

# session cookie for browser login (see _check_auth); only used when a token is configured
_COOKIE_NAME = "pyobs_video_session"
_COOKIE_LIFETIME = 24 * 60 * 60  # 24 h, in seconds
# delay on a wrong login password, to slow brute force (compare is constant-time either way)
_LOGIN_FAILURE_SLEEP = 1.0


async def calc_expose_timeout(webcam: IExposureTime, *args: Any, **kwargs: Any) -> float:
    """Calculates timeout for grabe_image()."""
    if hasattr(webcam, "_exposure_time"):
        return 2.0 * webcam._exposure_time + 30.0
    else:
        return 30.0


class NextImage(NamedTuple):
    date_obs: str
    image_type: ImageType
    header_futures: dict[str, asyncio.Task[Any]]
    broadcast: bool


class ImageRequest:
    def __init__(self, broadcast: bool = True):
        self.broadcast: bool = broadcast
        self.image: Image | None = None
        self.filename: str | None = None


class LastImage(NamedTuple):
    data: NDArray[Any]
    image: Image | None
    jpeg: bytes | None
    filename: str | None
    date_obs: str


class BaseVideo(Module, ImageFitsHeaderMixin, IVideo, IImageType, metaclass=ABCMeta):
    """Base class for all webcam modules.

    The built-in HTTP server serves the MJPEG live view, the raw frame stream and cached FITS
    images. Set the ``token`` parameter to protect all of them: machine clients send
    ``Authorization: Bearer <token>`` (as :class:`pyobs.vfs.HttpFile` does), browsers log in once
    at ``/login`` and get an HMAC-signed session cookie that rides the same-origin ``<img>``
    requests. Without a token (the default), no auth is enforced.
    """

    __module__ = "pyobs.modules.camera"

    def __init__(
        self,
        http_port: int = 37077,
        interval: float = 0.5,
        video_path: str | None = "/webcam/video.mjpg",
        raw_path: str | None = "/webcam/video.raw",
        filenames: str = "/webcam/pyobs-{DAY-OBS|date:}-{FRAMENUM|string:04d}.fits",
        fits_namespaces: list[str] | None = None,
        fits_headers: dict[str, Any] | None = None,
        centre: tuple[float, float] | None = None,
        rotation: float = 0.0,
        cache_size: int = 5,
        flip: bool = False,
        sleep_time: int = 60,
        fits_header_timeout: float = 15.0,
        token: str | None = None,
        **kwargs: Any,
    ):
        """Creates a new BaseWebcam.

        On the receiving end, a VFS root with a HTTPFile must exist with the same name as in image_path and video_path,
        i.e. "webcam" in the default settings.

        Args:
            http_port: HTTP port for webserver.
            exposure_time: Initial exposure time.
            interval: Min interval for grabbing images.
            video_path: VFS path to video. None disables the MJPEG live view.
            raw_path: VFS path to the raw frame stream. None disables it.
            filename: Filename pattern for FITS images.
            fits_namespaces: List of namespaces for FITS headers that this camera should request.
            fits_headers: Additional FITS headers.
            centre: (x, y) tuple of camera centre.
            rotation: Rotation east of north.
            cache_size: Size of cache for previous images.
            flip: Whether to flip around Y axis.
            sleep_time: Time in s with inactivity after which the camera should go to sleep.
            fits_header_timeout: Maximum seconds to wait for a peer's FITS headers before skipping them.
            token: Shared secret required in the "Authorization: Bearer <token>" header (or a
                login-page cookie) for stream and data access. If None (default), no auth is enforced.
        """
        super().__init__(
            fits_namespaces=fits_namespaces,
            fits_headers=fits_headers,
            centre=centre,
            rotation=rotation,
            filenames=filenames,
            fits_header_timeout=fits_header_timeout,
            **kwargs,
        )

        # store
        self._is_listening = False
        self._port = http_port
        self._interval = interval
        self._video_path = video_path
        self._raw_path = raw_path
        self._frame_num = 0
        self._image_type = ImageType.OBJECT
        self._image_request_lock = asyncio.Lock()
        self._activation_lock = asyncio.Lock()
        self._image_requests: list[ImageRequest] = []
        self._next_image: NextImage | None = None
        self._last_image: LastImage | None = None
        # lazy per-frame cache for raw_handler: the first of N simultaneous raw
        # consumers to wake for a given frame computes (meta, frame) bytes and the
        # rest reuse it, instead of each redoing the header build/JSON/copy (#769)
        self._raw_frame_cache: tuple[int, bytes, bytes] | None = None
        self._last_time = 0.0
        self._flip = flip
        # 60s is a starting point, not measured -- trades off against _activate_camera()/
        # _deactivate_camera() cost, which is driver-specific and mostly unknown right now;
        # too short relative to that cost risks flapping (rapid activate/deactivate cycling)
        self._sleep_time = sleep_time
        self._new_frame = asyncio.Event()

        # active
        self._active = False
        self._active_time = 0.0
        self.add_background_task(self._active_update)

        # image cache
        self._cache = DataCache(cache_size)

        # define web server
        self._token = token
        # serializes /login attempts so _LOGIN_FAILURE_SLEEP actually caps the guess rate;
        # without it, concurrent connections each sleep independently and the rate scales
        # with concurrency instead of being capped
        self._login_lock = asyncio.Lock()
        self._app = web.Application()
        routes = [web.get("/ping", self.ping_handler), web.get("/{filename}", self.image_handler)]
        if self._video_path is not None:
            routes += [web.get("/", self.web_handler), web.get("/video.mjpg", self.video_handler)]
        if self._raw_path is not None:
            routes.append(web.get("/video.raw", self.raw_handler))
        if self._token is not None:
            routes += [
                web.get("/login", self.login_handler),
                web.post("/login", self.login_post_handler),
                web.get("/logout", self.logout_handler),
            ]
        self._app.add_routes(routes)
        self._runner = web.AppRunner(self._app)
        self._site: web.TCPSite | None = None

    async def open(self) -> None:
        """Open module."""
        await Module.open(self)

        # start listening
        log.info("Starting HTTP file cache on port %d...", self._port)
        await self._runner.setup()
        self._site = web.TCPSite(self._runner, "0.0.0.0", self._port)
        await self._site.start()
        self._is_listening = True

        # declare that we send NewImageEvent, so peers (e.g. a GUI) actually subscribe to it --
        # see basecamera.py's equivalent registration
        await self.comm.register_event(NewImageEvent)

        # publish video URLs as capabilities
        await self.comm.set_capabilities(IVideo, VideoCapabilities(mjpeg=self._video_path, raw=self._raw_path))

        # publish initial state
        await self.comm.set_state(IImageType, ImageTypeState(image_type=self._image_type))

    async def close(self) -> None:
        """Close server"""
        await Module.close(self)

        # stop server
        await self._runner.cleanup()

    @property
    def opened(self) -> bool:
        """Whether the server is started."""
        return self._is_listening

    def _sign(self, expiry: int) -> str:
        """HMAC-SHA256 of ``expiry``, keyed with the configured token, as a hex digest.

        Shared by _make_session_value (signs) and _check_cookie (verifies), so the two can't
        drift apart on hash algo/encoding.

        Args:
            expiry: Session expiry timestamp being signed.

        Returns:
            Hex-encoded HMAC signature.
        """
        token = self._token
        if token is None:
            raise ValueError("Cannot sign a session without a configured token.")
        return hmac.new(token.encode(), str(expiry).encode(), hashlib.sha256).hexdigest()

    def _make_session_value(self) -> str:
        """Build the value for the login session cookie.

        Stateless and HMAC-signed -- the cookie does not contain the token itself:

        ``value = "{expiry_ts}.{hex}"`` where ``hex = HMAC-SHA256(key=token, msg=str(expiry_ts))``

        Returns:
            Cookie value.
        """
        expiry = int(time.time()) + _COOKIE_LIFETIME
        return f"{expiry}.{self._sign(expiry)}"

    def _check_bearer(self, request: web.Request) -> bool:
        """Whether the request carries the token as "Authorization: Bearer <token>".

        Only called (via _check_auth) once a token is configured.

        Args:
            request: Request to check.

        Returns:
            True if the header matches the configured token.
        """
        prefix = "Bearer "
        header = request.headers.get("Authorization", "")
        if not header.startswith(prefix):
            return False
        return hmac.compare_digest(header[len(prefix) :], self._token or "")

    def _check_cookie(self, request: web.Request) -> bool:
        """Whether the request carries a valid, unexpired session cookie.

        Only called (via _check_auth) once a token is configured.

        Args:
            request: Request to check.

        Returns:
            True if the cookie's HMAC signature verifies and it has not expired.
        """
        value = request.cookies.get(_COOKIE_NAME)
        if value is None:
            return False
        try:
            expiry_str, signature = value.rsplit(".", 1)
            expiry = int(expiry_str)
        except ValueError:
            return False
        if expiry < time.time():
            return False
        return hmac.compare_digest(signature, self._sign(expiry))

    def _check_auth(self, request: web.Request) -> None:
        """Raises HTTPUnauthorized if a token is configured and the request doesn't carry it.

        Accepts either a valid "Authorization: Bearer <token>" header or a valid session cookie.
        No-op when no token is configured. Same contract as HttpFileCache._check_auth: the
        exception type is identical regardless of which handler called it.

        Args:
            request: Request to check.
        """
        if self._token is None:
            return
        if not (self._check_bearer(request) or self._check_cookie(request)):
            raise web.HTTPUnauthorized()

    async def login_handler(self, request: web.Request) -> web.Response:
        """Handles GET access to /login and returns the login form.

        Served unauthenticated: this is the bootstrap a browser needs, since it cannot attach an
        "Authorization" header to an <img> request. Only registered when a token is configured.

        Args:
            request: Request to respond to.

        Returns:
            Response containing the login form.
        """
        html = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8">
    <title>Login</title>
  </head>
  <body>
    <form method="post" action="/login">
      <label>Password: <input type="password" name="token" autofocus></label>
      <button type="submit">Login</button>
    </form>
  </body>
</html>
"""
        return web.Response(text=html, content_type="text/html")

    async def login_post_handler(self, request: web.Request) -> web.Response:
        """Handles POST access to /login, verifying the password and issuing the session cookie.

        Args:
            request: Request to respond to.

        Returns:
            303 redirect to / on success, 401 on wrong password.
        """
        token = self._token
        if token is None:
            # login routes are only registered when a token is configured -- defensive
            raise web.HTTPUnauthorized()
        data = await request.post()
        password = str(data.get("token", ""))
        async with self._login_lock:
            # serialized: caps the guess rate at 1/_LOGIN_FAILURE_SLEEP regardless of how many
            # connections attempt concurrently
            if not hmac.compare_digest(password, token):
                # the compare above is constant-time; this sleep additionally slows brute force
                await asyncio.sleep(_LOGIN_FAILURE_SLEEP)
                raise web.HTTPUnauthorized()
        response = web.HTTPSeeOther("/")
        response.set_cookie(
            _COOKIE_NAME,
            self._make_session_value(),
            max_age=_COOKIE_LIFETIME,
            path="/",
            httponly=True,
            samesite="Lax",
        )
        return response

    async def logout_handler(self, request: web.Request) -> web.Response:
        """Handles GET access to /logout and clears the session cookie.

        Args:
            request: Request to respond to.

        Returns:
            303 redirect to /login.
        """
        response = web.HTTPSeeOther("/login")
        response.del_cookie(_COOKIE_NAME, path="/")
        return response

    async def web_handler(self, request: web.Request) -> web.Response:
        """Handles access to / and returns HTML page.

        Args:
            request: Request to respond to.

        Returns:
            Response containing web page.
        """
        # a browser landing on / should be taken to the login form, not shown a bare 401
        try:
            self._check_auth(request)
        except web.HTTPUnauthorized:
            raise web.HTTPSeeOther("/login")
        return web.Response(text=INDEX_HTML, content_type="text/html")

    async def ping_handler(self, request: web.Request) -> web.Response:
        """Handles GET access to /ping for testing connectivity.

        Args:
            request: Request to respond to.

        Returns:
            Response with a JSON status.
        """
        return web.json_response({"status": "ok"})

    async def video_handler(self, request: web.Request) -> web.StreamResponse:
        """Handles access to /video.mjpg and returns the video.

        Args:
            request: Request to respond to.

        Returns:
            Response containing video stream.
        """
        self._check_auth(request)

        # create response
        response = web.StreamResponse()
        response.content_type = "multipart/x-mixed-replace; boundary=--jpgboundary"
        await response.prepare(request)

        last_num = None
        last_time = 0.0
        while True:
            # not reached interval?
            if time.time() < last_time + self._interval:
                await asyncio.sleep(0.01)
                continue

            # get image
            num, image = await self.image_jpeg()
            if image is None:
                await asyncio.sleep(0.01)
                continue

            # is it actually a new image?
            if num == last_num:
                await asyncio.sleep(0.01)
                continue

            # now send image!
            last_num = num
            last_time = time.time()
            try:
                await response.write(b"--jpgboundary\r\nContent-type: image/jpeg\r\n\r\n" + image + b"\r\n")
            except aiohttp.client_exceptions.ClientConnectionResetError:
                # end stream
                break

        # return response
        return response

    async def raw_handler(self, request: web.Request) -> web.StreamResponse:
        """Handles access to /video.raw and returns raw frames.

        Args:
            request: Request to respond to.

        Returns:
            Response containing raw frame stream.
        """
        # auth first: an unauthenticated request must not wake the camera
        self._check_auth(request)

        # activate camera
        await self.activate_camera()

        # create response
        response = web.StreamResponse()
        response.content_type = "multipart/x-mixed-replace; boundary=--rawboundary"
        await response.prepare(request)

        while True:
            # wait for a new frame; the event coalesces multiple frames that
            # arrive while a slow consumer is still writing into a single wake.
            # Bounded by a timeout so a connected-but-frame-less stretch (producer
            # paused, exposure gap) still re-touches activity -- otherwise the
            # camera could go back to sleep out from under an active raw consumer
            # even though the connection is still open (design doc §5).
            try:
                await asyncio.wait_for(self._new_frame.wait(), timeout=self._sleep_time / 2)
            except TimeoutError:
                await self.activate_camera()
                continue
            self._new_frame.clear()

            # keep activity fresh for the duration of this connection
            await self.activate_camera()

            # get current frame
            last = self._last_image
            if last is None:
                continue

            # build frame bytes (JSON meta header + raw little-endian bytes), reusing
            # the cached result if another consumer already built this frame -- safe
            # without a lock since _raw_frame() is synchronous, so no other task can
            # interleave between the cache check and the store (#769)
            cached = self._raw_frame_cache
            if cached is not None and cached[0] == self._frame_num:
                _, meta, frame = cached
            else:
                meta, frame = self._raw_frame(last.data, last.date_obs)
                self._raw_frame_cache = (self._frame_num, meta, frame)

            # now send it!
            try:
                await response.write(
                    b"--rawboundary\r\n"
                    b"Content-Type: application/octet-stream\r\n"
                    b"X-Pyobs-Frame-Meta: " + meta + b"\r\n\r\n" + frame + b"\r\n"
                )
            except aiohttp.client_exceptions.ClientConnectionResetError:
                # end stream
                break

        # return response
        return response

    def _raw_frame(self, data: NDArray[Any], date_obs: str) -> tuple[bytes, bytes]:
        """Build the JSON meta header and raw bytes for one frame.

        Args:
            data: Numpy array to send.
            date_obs: Acquisition timestamp, captured in _set_image() -- not send time.

        Returns:
            Tuple of (meta header bytes, raw frame bytes).
        """

        # build a header using the same cheap, local sub-step as grab_data()'s FITS
        # path (no VFS I/O, no cross-module comm) -- see design doc §3
        image = Image(data)
        image.header["DATE-OBS"] = date_obs
        image.header["IMAGETYP"] = self._image_type
        self.add_local_fits_headers(image)

        # serialize header as a JSON dict, carrying DTYPE so the consumer can
        # decode the raw bytes unambiguously (numpy's dtype string bakes in byte order)
        meta: dict[str, Any] = {}
        for key in image.header:
            meta[key] = self._json_safe(image.header[key])
        meta["DTYPE"] = data.dtype.newbyteorder("<").str
        meta_bytes = json.dumps(meta, separators=(",", ":")).encode()

        # raw bytes, forced to little-endian regardless of host order
        frame = np.ascontiguousarray(data, dtype=data.dtype.newbyteorder("<")).tobytes()

        return meta_bytes, frame

    @staticmethod
    def _json_safe(value: Any) -> Any:
        """Convert a FITS header value to a JSON-serializable Python scalar."""
        if isinstance(value, np.generic):
            return value.item()
        return str(value) if isinstance(value, StrEnum) else value

    async def image_handler(self, request: web.Request) -> web.Response:
        """Handles access to /* and returns a specified image.

        Args:
            request: Request to respond to.

        Returns:
            Response containing image.
        """
        self._check_auth(request)

        # get filename
        filename = request.match_info["filename"]

        # get data
        if filename not in self._cache:
            raise web.HTTPNotFound()
        data = self._cache[filename]

        # send it
        log.info("Serving file %s.", filename)
        return web.Response(body=data, content_type="image/fits")

    @property
    def camera_active(self) -> bool:
        """Whether camera is currently active."""
        return self._active

    async def activate_camera(self) -> None:
        """Activate camera."""
        self._active_time = time.time()
        async with self._activation_lock:
            if not self._active:
                await self._activate_camera()
            self._active = True

    async def deactivate_camera(self) -> None:
        """Deactivate camera."""
        self._active_time = 0
        async with self._activation_lock:
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

    async def image_jpeg(self) -> tuple[int | None, bytes | None]:
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
            PIL.Image.fromarray(np.flip(data, axis=0)).save(output, format="jpeg")
            return output.getvalue()

    async def _set_image(self, data: NDArray[Any]) -> None:
        """Create FITS and JPEG images from data."""

        # capture acquisition time now, not when a raw-stream consumer later sends it
        date_obs = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%f")

        # flip image?
        if self._flip:
            data: NDArray[Any] = np.flip(data, axis=0)

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
                    await asyncio.sleep(0.02)

        # convert to jpeg only if we need live view
        now = time.time()
        jpeg = None
        if self._video_path is not None:
            # check interval
            if now - self._last_time > self._interval:
                # write to buffer and reset interval
                loop = asyncio.get_running_loop()
                jpeg = await loop.run_in_executor(None, self.create_jpeg, data)
                self._last_time = now

        # store both
        self._last_image = LastImage(data=data, image=image, jpeg=jpeg, filename=filename, date_obs=date_obs)
        self._frame_num += 1

        # signal any raw-stream consumers that a new frame is available
        self._new_frame.set()

        # prepare next image
        if len(self._image_requests) > 0:
            # broadcast?
            broadcast = any([req.broadcast for req in self._image_requests])

            # store everything
            logging.info("Preparing to catch next image...")
            self._next_image = NextImage(
                date_obs=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%f"),
                image_type=self._image_type,
                header_futures=await self.request_fits_headers(),
                broadcast=broadcast,
            )

    async def _create_image(self, data: NDArray[Any], next_image: NextImage) -> tuple[Image, str]:
        """Create an Image object from numpy array.

        Args:
            data: Numpy array to convert to Image.

        Returns:
            Tuple with image itself and the filename.
        """

        # create image
        image = Image(data)
        image.header["DATE-OBS"] = next_image.date_obs
        image.header["IMAGETYP"] = next_image.image_type

        # add fits headers and format filename
        await self.add_requested_fits_headers(image, next_image.header_futures)
        await self.add_fits_headers(image)

        # finish it up
        return await self._finish_image(image, next_image.broadcast, next_image.image_type)

    async def _finish_image(self, image: Image, broadcast: bool, image_type: ImageType) -> tuple[Image, str]:
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
        if filename is None:
            filename = "image.fits"
            image.header["FNAME"] = filename

        # store it and return filename
        log.info("Writing image %s to cache...", filename)
        loop = asyncio.get_running_loop()
        data = await loop.run_in_executor(None, image.to_bytes)
        self._cache[image.header["FNAME"]] = data

        # broadcast image path
        if broadcast and self._comm:
            log.info("Broadcasting image ID...")
            await self.comm.send_event(NewImageEvent(filename, image_type))

        # finished
        return image, filename

    @timeout(calc_expose_timeout)
    async def grab_data(self, broadcast: bool = True, **kwargs: Any) -> str:
        """Grabs an image ans returns reference.

        Args:
            broadcast: Broadcast existence of image.

        Returns:
            Name of image that was taken.

        Raises:
            GrabImageError: If there was a problem grabbing the image.
        """

        # activate camera
        await self.activate_camera()

        # acquire lock
        async with self._image_request_lock:
            # request new image
            image_request = ImageRequest(broadcast)
            self._image_requests.append(image_request)

        # we want an image that starts exposing AFTER now, so we wait for the current image to finish.
        log.info("Waiting for image to finish...")
        while image_request.image is None:
            await asyncio.sleep(0.01)

        # remove from list
        async with self._image_request_lock:
            self._image_requests.remove(image_request)

        # no image?
        if image_request.image is None or image_request.filename is None:
            raise exc.GrabImageError("Could not take image.")

        # finished
        return image_request.filename

    async def set_image_type(self, image_type: ImageType, **kwargs: Any) -> None:
        """Set the image type.

        Args:
            image_type: New image type.
        """
        log.info("Setting image type to %s...", image_type)
        self._image_type = image_type
        await self.comm.set_state(IImageType, ImageTypeState(image_type=image_type))
