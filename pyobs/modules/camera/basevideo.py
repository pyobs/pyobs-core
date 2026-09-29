import asyncio
import hashlib
import hmac
import io
import json
import logging
import time
from abc import ABCMeta
from collections.abc import AsyncIterator, Awaitable, Callable
from enum import StrEnum
from typing import Any, NamedTuple

import aiohttp
import numpy as np
import PIL.Image
from aiohttp import web
from astropy.table import Table
from astropy.time import TimeDelta
from numpy.typing import NDArray

from pyobs.events import NewImageEvent
from pyobs.images import Image
from pyobs.images.meta import DataPipelineName
from pyobs.interfaces import (
    DataStackState,
    IDataStack,
    IExposureTime,
    IImageType,
    ImageTypeState,
    IResettable,
    IVideo,
    VideoCapabilities,
    default_reset,
)
from pyobs.mixins.datapipeline import DataPipelineMixin
from pyobs.mixins.fitsheader import ImageFitsHeaderMixin
from pyobs.modules import Module, timeout
from pyobs.utils import exceptions as exc
from pyobs.utils.cache import DataCache
from pyobs.utils.enums import ImageType
from pyobs.utils.stretch import StretchParams, downsample, stretch_to_uint8
from pyobs.utils.time import Time

from .videoframes import Frame, FrameBuffer, FrameRecord, FramesDroppedError, StartSource

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
# while waiting for frames, re-touch camera activity this often, so a long exposure or stack
# doesn't let the camera fall asleep under a waiting grab_data()/grab_stack()
_KEEPALIVE_INTERVAL = 1.0
# back-off limits for restarting a failing frames() iterator
_FRAME_LOOP_MIN_BACKOFF = 1.0
_FRAME_LOOP_MAX_BACKOFF = 30.0
# per-frame caches for the live view (JPEG per stretch setting, raw bytes per crop/binning);
# pruned to the current frame once they hold more distinct settings than this
_MAX_CACHED_SETTINGS = 32


def _frame_time(webcam: Any) -> float:
    """Best guess for the current frame time: the driver's _exposure_time, else the exposure time
    of the newest frame, else 1s."""
    if getattr(webcam, "_exposure_time", None) is not None:
        return float(webcam._exposure_time)
    frames = getattr(webcam, "_frames", None)
    latest = frames.latest() if frames is not None else None
    if latest is not None and latest.exposure_time is not None:
        return latest.exposure_time
    return 1.0


async def calc_expose_timeout(webcam: IExposureTime, *args: Any, **kwargs: Any) -> float:
    """Calculates timeout for grab_data(). Up to three frame times: the frame exposing when the
    request comes in, the one-frame margin for estimated start times, and the frame itself."""
    return 3.0 * _frame_time(webcam) + 30.0


async def calc_video_stack_timeout(webcam: "BaseVideo", count: int = 1, *args: Any, **kwargs: Any) -> float:
    """Calculates timeout for grab_stack(). Two extra frames, see calc_expose_timeout()."""
    return (count + 2) * (_frame_time(webcam) + webcam._stack_frame_overhead) + webcam._stack_timeout_margin


class NextImage(NamedTuple):
    """Everything _create_image() needs besides the data, collected by grab_data()."""

    date_obs: str
    image_type: ImageType
    header_futures: dict[str, asyncio.Task[Any]]
    broadcast: bool
    pipeline: str | None
    exposure_time: float | None = None
    date_src: StartSource | None = None
    date_arrival: str | None = None
    frame_number: int | None = None


class BaseVideo(
    Module, ImageFitsHeaderMixin, IVideo, IImageType, IResettable, DataPipelineMixin, IDataStack, metaclass=ABCMeta
):
    """Base class for all webcam modules.

    Drivers implement :meth:`frames`, an async iterator yielding :class:`~pyobs.modules.camera.videoframes.Frame`
    objects; BaseVideo runs it while the camera is active and puts every frame into a small ring
    buffer, from which grab_data(), grab_stack(), the MJPEG live view and the raw stream read.
    Drivers that still push frames themselves via :meth:`_set_image` keep working, but that path is
    deprecated.

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
        max_stack_bytes: int = 2 * 1024**3,
        stack_frame_overhead: float = 2.0,
        stack_timeout_margin: float = 60.0,
        buffer_frames: int = 4,
        readout_time: float = 0.0,
        stretch: str = "linear",
        cuts: str | None = None,
        cut_lo: float | None = None,
        cut_hi: float | None = None,
        jpeg_quality: int = 80,
        **kwargs: Any,
    ):
        """Creates a new BaseWebcam.

        On the receiving end, a VFS root with a HTTPFile must exist with the same name as in image_path and video_path,
        i.e. "webcam" in the default settings.

        Args:
            http_port: HTTP port for webserver.
            interval: Min interval between two frames sent to one MJPEG live-view connection.
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
            max_stack_bytes: Memory cap for a grab_stack() cube (count * frame size), in bytes.
                A stacked product also sits in the in-memory DataCache (cache_size) once stored,
                so peak memory use with several cached stacks can be well above this cap.
            stack_frame_overhead: Estimated per-frame overhead in seconds, added to the frame
                interval when computing grab_stack()'s timeout.
            stack_timeout_margin: Extra seconds added to grab_stack()'s timeout, covering header
                requests, cube assembly and the data pipeline.
            buffer_frames: Number of recent frames kept in memory for grab_data(), grab_stack()
                and the streams. grab_stack() fails if it falls behind by more than this.
            readout_time: Readout time in seconds, used to estimate a frame's exposure start when
                the driver doesn't provide one (start = arrival - exposure time - readout time).
            stretch: Default stretch function for the MJPEG live view (linear, sqrt, asinh, log).
            cuts: Default cuts for the MJPEG live view (full, minmax, percentile, manual). None
                means "full" for 8-bit data and "minmax" otherwise.
            cut_lo: Default low cut (percentile or value, depending on cuts).
            cut_hi: Default high cut (percentile or value, depending on cuts).
            jpeg_quality: Default JPEG quality for the MJPEG live view.
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
        self._image_type = ImageType.OBJECT
        self._activation_lock = asyncio.Lock()
        self._max_stack_bytes = max_stack_bytes
        self._stack_frame_overhead = stack_frame_overhead
        self._stack_timeout_margin = stack_timeout_margin
        self._flip = flip
        self._readout_time = readout_time
        # 60s is a starting point, not measured -- trades off against _activate_camera()/
        # _deactivate_camera() cost, which is driver-specific and mostly unknown right now;
        # too short relative to that cost risks flapping (rapid activate/deactivate cycling)
        self._sleep_time = sleep_time

        # frames: ring buffer, next frame number, settings generation, the frames() loop task,
        # and whether the deprecated _set_image() path has already been warned about
        self._frames = FrameBuffer(buffer_frames)
        self._frame_num = 0
        self._generation = 0
        self._frame_loop_task: asyncio.Task[None] | None = None
        self._set_image_warned = False

        # a running stack's abort flag, None if no stack is running
        self._stack_abort: asyncio.Event | None = None

        # live view defaults, validated right away so a bad config fails at startup
        self._stretch = StretchParams(stretch=stretch, cuts=cuts, lo=cut_lo, hi=cut_hi)  # type: ignore[arg-type]
        if not 1 <= jpeg_quality <= 95:
            raise ValueError("jpeg_quality must be between 1 and 95.")
        self._jpeg_quality = jpeg_quality

        # per-frame caches shared by all stream connections (#769): the first connection to need
        # a frame in a given setting computes it, the others reuse it
        self._jpeg_cache: dict[tuple[StretchParams, int], tuple[int, asyncio.Future[bytes]]] = {}
        self._raw_frame_cache: dict[tuple[tuple[int, int, int, int] | None, int], tuple[int, bytes, bytes]] = {}

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
        await self._datapipeline_open()
        await self.comm.set_state(IDataStack, DataStackState(count_total=0, count_left=0))

    async def close(self) -> None:
        """Close server"""
        await self._stop_frame_loop()
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

        Optional query parameters set the stretch for this connection (defaults from the module
        config): ``stretch``, ``cuts``, ``lo``, ``hi``, ``scale`` (downsampling factor) and
        ``quality`` (JPEG quality). Connections with the same settings share the encoding work.

        Args:
            request: Request to respond to.

        Returns:
            Response containing video stream.
        """
        self._check_auth(request)
        params, quality = self._parse_jpeg_params(request)

        # create response
        response = web.StreamResponse()
        response.content_type = "multipart/x-mixed-replace; boundary=--jpgboundary"
        await response.prepare(request)

        last_num = -1
        last_time = 0.0
        while True:
            # not reached interval?
            wait = last_time + self._interval - time.time()
            if wait > 0:
                await asyncio.sleep(wait)

            # keep camera awake while someone is watching, and wait for a new frame; bounded, so a
            # frame-less stretch still re-touches activity
            await self.activate_camera()
            try:
                record = await asyncio.wait_for(self._frames.wait_newer(last_num), timeout=self._sleep_time / 2)
            except TimeoutError:
                continue

            # encode (or reuse another connection's encoding of this frame)
            try:
                jpeg = await self._jpeg_for(record, params, quality)
            except ValueError as e:
                log.warning("Could not encode live view frame, closing stream: %s", e)
                break

            # now send image!
            last_num = record.number
            last_time = time.time()
            try:
                await response.write(b"--jpgboundary\r\nContent-type: image/jpeg\r\n\r\n" + jpeg + b"\r\n")
            except aiohttp.client_exceptions.ClientConnectionResetError:
                # end stream
                break

        # return response
        return response

    def _parse_jpeg_params(self, request: web.Request) -> tuple[StretchParams, int]:
        """Parse the live view's stretch settings from the query, falling back to module defaults.

        Raises:
            HTTPBadRequest: If a parameter is invalid.
        """
        q = request.query
        d = self._stretch
        try:
            params = StretchParams(
                stretch=q.get("stretch", d.stretch),  # type: ignore[arg-type]
                cuts=q.get("cuts", d.cuts),  # type: ignore[arg-type]
                lo=float(q["lo"]) if "lo" in q else d.lo,
                hi=float(q["hi"]) if "hi" in q else d.hi,
                scale=int(q["scale"]) if "scale" in q else d.scale,
            )
            quality = int(q["quality"]) if "quality" in q else self._jpeg_quality
        except ValueError as e:
            raise web.HTTPBadRequest(text=f"Invalid live view parameter: {e}")
        if not 1 <= quality <= 95:
            raise web.HTTPBadRequest(text="quality must be between 1 and 95.")
        return params, quality

    async def _jpeg_for(self, record: FrameRecord, params: StretchParams, quality: int) -> bytes:
        """Return the JPEG for a frame in the given setting, encoding it at most once per frame."""
        key = (params, quality)
        entry = self._jpeg_cache.get(key)
        if entry is not None and entry[0] == record.number:
            return await entry[1]

        loop = asyncio.get_running_loop()
        future = loop.run_in_executor(None, self.create_jpeg, record.data, params, quality)
        self._jpeg_cache[key] = (record.number, future)
        if len(self._jpeg_cache) > _MAX_CACHED_SETTINGS:
            self._jpeg_cache = {k: v for k, v in self._jpeg_cache.items() if v[0] == record.number}
        return await future

    async def raw_handler(self, request: web.Request) -> web.StreamResponse:
        """Handles access to /video.raw and returns raw frames.

        Optional query parameters: ``x``, ``y``, ``w``, ``h`` crop the frame (unbinned pixels, all
        four or none), ``bin`` bins it in software (block mean, after cropping), ``max_rate`` caps
        the frames per second sent to this connection (newest frame wins).

        Args:
            request: Request to respond to.

        Returns:
            Response containing raw frame stream.
        """
        # auth first: an unauthenticated request must not wake the camera
        self._check_auth(request)
        crop, binning, max_rate = self._parse_raw_params(request)

        # activate camera
        await self.activate_camera()

        # create response
        response = web.StreamResponse()
        response.content_type = "multipart/x-mixed-replace; boundary=--rawboundary"
        await response.prepare(request)

        last_num = -1
        last_time = 0.0
        while True:
            # rate limit for this connection
            if max_rate is not None:
                wait = last_time + 1.0 / max_rate - time.time()
                if wait > 0:
                    await asyncio.sleep(wait)

            # wait for a new frame; latest-wins, so frames that arrive while a slow consumer is
            # still writing are skipped. Bounded by a timeout so a connected-but-frame-less stretch
            # (producer paused, exposure gap) still re-touches activity -- otherwise the camera
            # could go back to sleep out from under an active raw consumer even though the
            # connection is still open (see basevideo-raw-frame-streaming design doc §5).
            try:
                record = await asyncio.wait_for(self._frames.wait_newer(last_num), timeout=self._sleep_time / 2)
            except TimeoutError:
                await self.activate_camera()
                continue

            # keep activity fresh for the duration of this connection
            await self.activate_camera()

            # build frame bytes (JSON meta header + raw little-endian bytes), reusing the cached
            # result if another consumer already built this frame in the same crop/binning --
            # safe without a lock since _raw_frame() is synchronous (#769)
            key = (crop, binning)
            cached = self._raw_frame_cache.get(key)
            if cached is not None and cached[0] == record.number:
                _, meta, frame = cached
            else:
                try:
                    meta, frame = self._raw_frame(record, crop, binning)
                except ValueError as e:
                    log.warning("Could not build raw frame, closing stream: %s", e)
                    break
                self._raw_frame_cache[key] = (record.number, meta, frame)
                if len(self._raw_frame_cache) > _MAX_CACHED_SETTINGS:
                    self._raw_frame_cache = {k: v for k, v in self._raw_frame_cache.items() if v[0] == record.number}

            # now send it!
            last_num = record.number
            last_time = time.time()
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

    @staticmethod
    def _parse_raw_params(
        request: web.Request,
    ) -> tuple[tuple[int, int, int, int] | None, int, float | None]:
        """Parse crop, binning and rate limit for the raw stream from the query.

        Raises:
            HTTPBadRequest: If a parameter is invalid.
        """
        q = request.query
        try:
            crop_keys = [k for k in ("x", "y", "w", "h") if k in q]
            crop: tuple[int, int, int, int] | None = None
            if crop_keys:
                if len(crop_keys) != 4:
                    raise ValueError("crop needs all of x, y, w, h")
                x, y, w, h = (int(q[k]) for k in ("x", "y", "w", "h"))
                if x < 0 or y < 0 or w < 1 or h < 1:
                    raise ValueError("crop needs x, y >= 0 and w, h >= 1")
                crop = (x, y, w, h)
            binning = int(q.get("bin", "1"))
            if binning < 1:
                raise ValueError("bin must be >= 1")
            max_rate = float(q["max_rate"]) if "max_rate" in q else None
            if max_rate is not None and max_rate <= 0:
                raise ValueError("max_rate must be > 0")
        except ValueError as e:
            raise web.HTTPBadRequest(text=f"Invalid raw stream parameter: {e}")
        return crop, binning, max_rate

    def _raw_frame(
        self, record: FrameRecord, crop: tuple[int, int, int, int] | None = None, binning: int = 1
    ) -> tuple[bytes, bytes]:
        """Build the JSON meta header and raw bytes for one frame.

        Args:
            record: Frame to send.
            crop: Optional (x, y, w, h) crop in unbinned pixels, clipped to the frame.
            binning: Software binning factor (block mean), applied after cropping.

        Returns:
            Tuple of (meta header bytes, raw frame bytes).

        Raises:
            ValueError: If the crop lies completely outside the frame, or binning is larger than it.
        """
        data = record.data
        x0, y0 = 0, 0
        if crop is not None:
            x, y, w, h = crop
            height, width = data.shape[:2]
            x0, y0 = min(x, width), min(y, height)
            data = data[y0 : min(y0 + h, height), x0 : min(x0 + w, width)]
            if data.size == 0:
                raise ValueError("Crop lies outside the frame.")
        if binning > 1:
            data = downsample(data, binning)

        # build a header using the same cheap, local sub-step as grab_data()'s FITS path (no VFS
        # I/O, no cross-module comm) -- see basevideo-raw-frame-streaming design doc §3. The crop
        # origin goes in first, so CRPIX1/2 come out right for the cropped frame.
        image = Image(data)
        image.header["DATE-OBS"] = record.date_obs
        image.header["IMAGETYP"] = self._image_type
        if crop is not None:
            image.header["XORGSUBF"] = x0
            image.header["YORGSUBF"] = y0
        self.add_local_fits_headers(image)
        if binning > 1:
            for axis in ("1", "2"):
                if "CRPIX" + axis in image.header:
                    image.header["CRPIX" + axis] = image.header["CRPIX" + axis] / binning
                if "CDELT" + axis in image.header:
                    image.header["CDELT" + axis] = image.header["CDELT" + axis] * binning
                if "DET-BIN" + axis in image.header:
                    image.header["DET-BIN" + axis] = image.header["DET-BIN" + axis] * binning

        # serialize header as a JSON dict, carrying DTYPE so the consumer can decode the raw bytes
        # unambiguously (numpy's dtype string bakes in byte order), plus the frame bookkeeping
        meta: dict[str, Any] = {}
        for key in image.header:
            meta[key] = self._json_safe(image.header[key])
        meta["DTYPE"] = data.dtype.newbyteorder("<").str
        meta["VIDFRAME"] = record.number
        meta["DATE-SRC"] = str(record.start_source)
        meta["DATE-ARR"] = record.date_arrival
        if record.exposure_time is not None:
            meta["EXPTIME"] = record.exposure_time
        meta["SETGEN"] = record.generation
        meta["CROP-X"] = x0
        meta["CROP-Y"] = y0
        meta["SWBIN"] = binning
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
                self._start_frame_loop()
            self._active = True

    async def deactivate_camera(self) -> None:
        """Deactivate camera."""
        self._active_time = 0
        async with self._activation_lock:
            if self._active:
                await self._stop_frame_loop()
                await self._deactivate_camera()
            self._active = False

    async def _activate_camera(self) -> None:
        """Can be overridden by derived class to implement inactivity sleep.

        Drivers implementing frames() usually don't need this: acquisition starts when BaseVideo
        starts iterating frames() and stops when it closes the iterator.
        """
        pass

    async def _deactivate_camera(self) -> None:
        """Can be overridden by derived class to implement inactivity sleep, see _activate_camera()."""
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

    def frames(self) -> AsyncIterator[Frame]:
        """Yield frames from the camera, to be implemented by drivers as an async generator.

        BaseVideo starts iterating when the camera gets activated and closes the iterator
        (``aclose()``, i.e. GeneratorExit/CancelledError at the current ``await``) when it goes to
        sleep, so drivers start acquisition at the top and stop it in a ``finally`` block. If the
        iterator raises, it is restarted with a back-off.

        Blocking SDK calls must not run on the event loop; use a worker thread.

        Drivers that don't implement this push frames via the deprecated :meth:`_set_image`.
        """
        raise NotImplementedError

    @property
    def _has_frame_iterator(self) -> bool:
        """Whether the driver implements frames()."""
        return type(self).frames is not BaseVideo.frames

    def _start_frame_loop(self) -> None:
        """Start iterating frames(), if the driver implements it and it isn't running yet."""
        if not self._has_frame_iterator:
            return
        if self._frame_loop_task is None or self._frame_loop_task.done():
            self._frame_loop_task = asyncio.create_task(self._frame_loop())

    async def _stop_frame_loop(self) -> None:
        """Stop iterating frames(), closing the driver's iterator."""
        task, self._frame_loop_task = self._frame_loop_task, None
        if task is None or task.done():
            return
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    async def _frame_loop(self) -> None:
        """Iterate the driver's frames() and put every frame into the buffer, restarting on errors."""
        backoff = _FRAME_LOOP_MIN_BACKOFF
        while True:
            iterator = self.frames()
            try:
                async for frame in iterator:
                    await self._add_frame(frame)
                    backoff = _FRAME_LOOP_MIN_BACKOFF
                log.warning("Frame iterator ended, restarting in %.0fs...", backoff)
            except asyncio.CancelledError:
                raise
            except Exception:
                log.exception("Error in frame iterator, restarting in %.0fs...", backoff)
            finally:
                aclose = getattr(iterator, "aclose", None)
                if aclose is not None:
                    await aclose()
            await asyncio.sleep(backoff)
            backoff = min(2 * backoff, _FRAME_LOOP_MAX_BACKOFF)

    async def _add_frame(self, frame: Frame) -> FrameRecord:
        """Put a frame into the buffer. Must stay cheap: runs once per frame on the event loop.

        Args:
            frame: New frame from the driver.

        Returns:
            The stored frame record.
        """
        arrival = time.time()

        # flip image? (a view, no copy)
        data: NDArray[Any] = np.flip(frame.data, axis=0) if self._flip else frame.data

        # exposure start: from the driver, else estimated, else unknown
        exposure_time = frame.exposure_time
        if frame.start is not None:
            start: float | None = frame.start
            source = StartSource.DEVICE
        elif exposure_time is not None:
            start = arrival - exposure_time - self._readout_time
            source = StartSource.ESTIMATED
        else:
            start = None
            source = StartSource.UNKNOWN

        record = FrameRecord(
            number=self._frame_num,
            data=data,
            arrival=arrival,
            start=start,
            start_source=source,
            exposure_time=exposure_time,
            generation=frame.generation if frame.generation is not None else self._generation,
        )
        self._frame_num += 1
        await self._frames.add(record)
        return record

    async def _set_image(self, data: NDArray[Any]) -> None:
        """Push a new frame. Deprecated: implement frames() instead.

        Kept for drivers that run their own capture loop. The frame gets no exposure start from the
        driver, only an estimate from the driver's ``_exposure_time`` attribute, if it has one.

        Args:
            data: New frame.
        """
        if not self._set_image_warned:
            log.warning(
                "%s pushes frames via _set_image(), which is deprecated; implement frames().", type(self).__name__
            )
            self._set_image_warned = True
        exposure_time = getattr(self, "_exposure_time", None)
        await self._add_frame(Frame(data=data, exposure_time=exposure_time))

    def _new_generation(self) -> int:
        """Start a new settings generation. Drivers call this whenever they change a setting that
        affects the image (exposure time, gain, window, binning, ...), and stamp frames taken with
        the new settings with the returned value.

        Returns:
            The new generation.
        """
        self._generation += 1
        return self._generation

    @property
    def generation(self) -> int:
        """Current settings generation."""
        return self._generation

    async def image_jpeg(self) -> tuple[int | None, bytes | None]:
        """Return the newest frame as JPEG with the module's default stretch."""

        # activate camera, first image will most probably be None
        await self.activate_camera()

        # return what we got
        record = self._frames.latest()
        if record is None:
            return None, None
        return record.number, await self._jpeg_for(record, self._stretch, self._jpeg_quality)

    @staticmethod
    def create_jpeg(data: NDArray[Any], params: StretchParams | None = None, quality: int = 80) -> bytes:
        """Create a JPEG image from a numpy array and return as bytes.

        Args:
            data: Numpy array to convert to JPEG.
            params: How to stretch the data to 8 bit, defaults if None.
            quality: JPEG quality.

        Returns:
            Bytes containing JPEG image.
        """
        data8 = stretch_to_uint8(data, params)
        with io.BytesIO() as output:
            PIL.Image.fromarray(np.flip(data8, axis=0)).save(output, format="jpeg", quality=quality)
            return output.getvalue()

    def _started_after(self, t0: float, n0: int, generation: int) -> Callable[[FrameRecord], bool]:
        """Predicate for "this frame started exposing after t0, with settings of this generation".

        With a device timestamp that's exact. With an estimated start, one frame time is added as
        margin for frames queued in the driver/SDK. Without any start time, the frame exposing when
        the request came in is skipped, i.e. the second frame after n0 is the first one accepted.

        Args:
            t0: Request time as UTC unix time.
            n0: Number of the newest frame at request time, -1 for none.
            generation: Minimum settings generation.
        """

        def predicate(record: FrameRecord) -> bool:
            if record.generation < generation:
                return False
            if record.start_source == StartSource.DEVICE and record.start is not None:
                return record.start >= t0
            if record.start_source == StartSource.ESTIMATED and record.start is not None:
                return record.start >= t0 + (record.exposure_time or 0.0)
            return record.number >= n0 + 2

        return predicate

    async def _wait_awake(
        self, factory: Callable[[], Awaitable[FrameRecord]], abort: asyncio.Event | None = None
    ) -> FrameRecord:
        """Wait for a frame, keeping the camera awake and reacting to an abort.

        Args:
            factory: Creates the awaitable to wait for; called again after every keep-alive.
            abort: Optional event that aborts the wait.

        Raises:
            AbortedError: If the abort event was set.
        """
        while True:
            if abort is not None and abort.is_set():
                raise exc.AbortedError("Stack was aborted.")
            waiter = asyncio.ensure_future(factory())
            waiters: set[asyncio.Future[Any]] = {waiter}
            abort_waiter = asyncio.ensure_future(abort.wait()) if abort is not None else None
            if abort_waiter is not None:
                waiters.add(abort_waiter)
            try:
                done, _ = await asyncio.wait(waiters, timeout=_KEEPALIVE_INTERVAL, return_when=asyncio.FIRST_COMPLETED)
            finally:
                pending = [w for w in waiters if not w.done()]
                for w in pending:
                    w.cancel()
                await asyncio.gather(*pending, return_exceptions=True)
            if waiter in done:
                return waiter.result()
            if abort_waiter is not None and abort_waiter in done:
                raise exc.AbortedError("Stack was aborted.")
            await self.activate_camera()

    async def _create_image(self, data: NDArray[Any], next_image: NextImage) -> tuple[Image, str]:
        """Create an Image object from numpy array.

        Args:
            data: Numpy array to convert to Image.
            next_image: Frame and request info collected by grab_data().

        Returns:
            Tuple with image itself and the filename.
        """

        # create image
        image = Image(data)
        image.header["DATE-OBS"] = next_image.date_obs
        image.header["IMAGETYP"] = next_image.image_type
        if next_image.exposure_time is not None:
            image.header["EXPTIME"] = (next_image.exposure_time, "Exposure time [s]")
        if next_image.date_src is not None:
            image.header["DATE-SRC"] = (str(next_image.date_src), "Source of DATE-OBS (device/estimated/unknown)")
        if next_image.date_arrival is not None:
            image.header["DATE-ARR"] = (next_image.date_arrival, "Time the frame arrived at the module")
        if next_image.frame_number is not None:
            image.header["VIDFRAME"] = (next_image.frame_number, "Frame number in video stream")
        image.set_meta(DataPipelineName(next_image.pipeline))

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

        Raises:
            GrabImageError: If the data pipeline failed. Nothing is stored in that case.
        """

        # run data pipeline -- replaces raw data with the pipeline's result. The pipeline name
        # travels as image meta rather than a parameter, so subclasses overriding this method's
        # signature (pyobs-aravis, pyobs-tis) keep working unchanged. Missing meta means a caller
        # bypassed _create_image() (e.g. pyobs-iagvt's GregoryCamera) -- fall back to whatever
        # pipeline is currently selected rather than silently running none.
        meta = image.get_meta_safe(DataPipelineName)
        pipeline = self._data_pipeline if meta is None else meta.name
        image = await self._run_data_pipeline(image, pipeline)

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
        """Grabs an image and returns reference.

        Returns the first frame that started exposing after this call, with the camera settings
        that were current at the time of the call. FITS headers from other modules are requested
        right away, i.e. before that exposure starts. Nothing of this runs in the frame loop, so the
        streams keep flowing while the image is built.

        Args:
            broadcast: Broadcast existence of image.

        Returns:
            Name of image that was taken.

        Raises:
            GrabImageError: If there was a problem grabbing the image.
        """

        # activate camera
        await self.activate_camera()

        # everything about this request is fixed now
        predicate = self._started_after(time.time(), self._frames.last_number, self._generation)
        image_type, pipeline = self._image_type, self._data_pipeline
        header_futures = await self.request_fits_headers()

        # wait for the first frame that started after now
        log.info("Waiting for next frame...")
        try:
            record = await self._wait_awake(lambda: self._frames.wait_frame(predicate))
        except BaseException:
            await self._cancel_header_requests(header_futures)
            raise

        # build image
        next_image = NextImage(
            date_obs=record.date_obs,
            image_type=image_type,
            header_futures=header_futures,
            broadcast=broadcast,
            pipeline=pipeline,
            exposure_time=record.exposure_time,
            date_src=record.start_source,
            date_arrival=record.date_arrival,
            frame_number=record.number,
        )
        try:
            _, filename = await self._create_image(record.data, next_image)
        except exc.PyobsError:
            raise
        except Exception as e:
            log.exception("Could not create image.")
            raise exc.GrabImageError(str(e)) from e
        return filename

    @timeout(calc_video_stack_timeout)
    async def grab_stack(self, count: int, broadcast: bool = True, **kwargs: Any) -> str:
        """Grab count consecutive frames into one product and return its name.

        Without a pipeline selected (IDataPipeline), the product is a 3D cube of all frames.
        With one, the pipeline runs on the cube (e.g. to combine it) and only its result is
        stored. Single grab_data() calls during a stack are still served concurrently.

        The first frame is chosen like in grab_data(); all following ones must be consecutive and
        taken with the same settings.

        Args:
            count: Number of frames.
            broadcast: Broadcast existence of the product.

        Returns:
            Name of the stored product.

        Raises:
            InvalidArgumentError: If count < 1, or the stack would exceed the module's memory cap.
            DeviceBusyError: If another stack is already running.
            AbortedError: If the stack was aborted.
            GrabImageError: If a frame could not be grabbed, frames were dropped or don't match,
                or the pipeline failed.
        """
        if count < 1:
            raise exc.InvalidArgumentError("count must be >= 1.")
        if self._stack_abort is not None:
            raise exc.DeviceBusyError("Cannot start new stack because one is already running.")

        # advisory check, using the size of the newest frame -- settings may have changed since
        # then, so this can only reject, never guarantee it's safe
        latest = self._frames.latest()
        if latest is not None and count * latest.data.nbytes > self._max_stack_bytes:
            raise exc.InvalidArgumentError(
                f"Stack of {count} frames would exceed the memory cap of {self._max_stack_bytes} bytes."
            )

        await self.activate_camera()

        abort = asyncio.Event()
        self._stack_abort = abort
        await self.comm.set_state(IDataStack, DataStackState(count_total=count, count_left=count))

        try:
            # fix everything about this request now, like grab_data()
            predicate = self._started_after(time.time(), self._frames.last_number, self._generation)
            image_type, pipeline = self._image_type, self._data_pipeline
            header_futures = await self.request_fits_headers()

            # collect frames
            try:
                records, cube = await self._collect_stack(predicate, count, abort)
            except BaseException:
                await self._cancel_header_requests(header_futures)
                raise
            first = records[0]

            # per-frame table; exposure times fall back to the stream's for drivers that don't report them
            fallback = _frame_time(self)
            exptimes = [r.exposure_time if r.exposure_time is not None else fallback for r in records]
            frames_table = Table(
                rows=[(i, r.date_obs, e) for i, (r, e) in enumerate(zip(records, exptimes))],
                names=("FRAME", "DATE-OBS", "EXPTIME"),
            )

            image = Image(cube, frames=frames_table)
            image.header["DATE-OBS"] = first.date_obs
            image.header["DATE-SRC"] = (str(first.start_source), "Source of DATE-OBS (device/estimated/unknown)")
            image.header["IMAGETYP"] = image_type
            image.header["CTYPE3"] = "FRAME"
            image.header["NFRAMES"] = count

            try:
                image.header["DATE-END"] = (Time(records[-1].date_obs) + TimeDelta(exptimes[-1], format="sec")).isot
            except ValueError:
                image.header["DATE-END"] = records[-1].date_obs

            await self.add_requested_fits_headers(image, header_futures)
            await self.add_fits_headers(image)
            image.set_meta(DataPipelineName(pipeline))

            _, filename = await self._finish_image(image, broadcast, image_type)
            return filename
        finally:
            self._stack_abort = None
            await self.comm.set_state(IDataStack, DataStackState(count_total=0, count_left=0))

    async def _collect_stack(
        self, predicate: Callable[[FrameRecord], bool], count: int, abort: asyncio.Event
    ) -> tuple[list[FrameRecord], NDArray[Any]]:
        """Collect count consecutive frames, starting with the first one matching predicate."""
        first = await self._wait_awake(lambda: self._frames.wait_frame(predicate), abort)
        records = [first]
        cube = self._start_cube(first, count)
        cube[0] = first.data  # copies
        await self._stack_progress(count, 1)
        while len(records) < count:
            previous = records[-1]
            try:
                record = await self._wait_awake(lambda: self._frames.next_after(previous.number), abort)
            except FramesDroppedError:
                raise exc.GrabImageError(
                    f"Frames were dropped during the stack (buffer of {self._frames.size} frames too small?)."
                )
            if record.generation != first.generation:
                raise exc.GrabImageError("Camera settings changed during stack.")
            if record.data.shape != cube.shape[1:] or record.data.dtype != cube.dtype:
                raise exc.GrabImageError("Frames in stack do not match in shape or dtype.")
            cube[len(records)] = record.data  # copies
            records.append(record)
            await self._stack_progress(count, len(records))
        return records, cube

    @staticmethod
    async def _cancel_header_requests(futures: dict[str, asyncio.Task[Any]]) -> None:
        """Cancel FITS header requests that won't be used anymore."""
        pending = [f for f in futures.values() if not f.done()]
        for f in pending:
            f.cancel()
        await asyncio.gather(*pending, return_exceptions=True)

    def _start_cube(self, first: FrameRecord, count: int) -> NDArray[Any]:
        """Allocate the stack cube from the first frame, checking it can be stacked at all."""
        if first.data.ndim != 2:
            raise exc.GrabImageError("Stacking color frames is not supported.")

        # authoritative memory check, now with the real frame size
        if count * first.data.nbytes > self._max_stack_bytes:
            raise exc.InvalidArgumentError(
                f"Stack of {count} frames would exceed the memory cap of {self._max_stack_bytes} bytes."
            )
        return np.empty((count, *first.data.shape), dtype=first.data.dtype)

    async def _stack_progress(self, count: int, collected: int) -> None:
        await self.comm.set_state(IDataStack, DataStackState(count_total=count, count_left=count - collected))

    async def set_image_type(self, image_type: ImageType, **kwargs: Any) -> None:
        """Set the image type.

        Args:
            image_type: New image type.
        """
        log.info("Setting image type to %s...", image_type)
        self._image_type = image_type
        await self.comm.set_state(IImageType, ImageTypeState(image_type=image_type))

    async def abort(self, **kwargs: Any) -> None:
        """Abort a running stack.

        Pending single grab_data() requests are not affected -- BaseVideo already serves those
        concurrently with a running stack.
        """
        if self._stack_abort is not None:
            log.info("Aborting stack...")
            self._stack_abort.set()

    @default_reset
    async def reset(self, **kwargs: Any) -> None:
        """Reset the image type to its default.

        Raises:
            DeviceBusyError: If a stack is currently running.
        """
        if self._stack_abort is not None:
            raise exc.DeviceBusyError("Cannot reset camera while a stack is running.")

        await self.set_image_type(ImageType.OBJECT)
        await self.set_pipeline(self._default_pipeline)

    @default_reset
    async def full_reset(self, **kwargs: Any) -> None:
        """Reset the camera completely to its configured defaults, hardware included.

        Raises:
            DeviceBusyError: If a stack is currently running.
        """
        await self.reset(**kwargs)
