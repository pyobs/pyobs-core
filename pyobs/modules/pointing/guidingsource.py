"""Where a guiding module gets its images from: a camera's grab_data(), or a video camera's raw stream.

See specs/design/guiding-raw-stream.md.
"""

from __future__ import annotations

import json
import logging
from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, Any, cast

import aiohttp
import numpy as np

from pyobs.comm.proxy import Proxy
from pyobs.images import Image
from pyobs.images.processors.detection import SepSourceDetection
from pyobs.interfaces import IData, IExposureTime, IImageType, IVideo
from pyobs.mixins.fitsheader import add_requested_fits_headers, request_fits_headers
from pyobs.utils import exceptions as exc
from pyobs.utils.enums import ImageType
from pyobs.utils.time import Time

if TYPE_CHECKING:
    from pyobs.modules import Module

log = logging.getLogger(__name__)

# boundary written by BaseVideo.raw_handler()
_RAW_BOUNDARY = b"--rawboundary"
# meta keys that describe the wire format, not the image; not copied into the FITS header
_WIRE_KEYS = {"DTYPE"}
# relative tolerance when comparing a frame's EXPTIME with the requested exposure time
_EXPTIME_TOLERANCE = 0.01


class GuidingFrameSource(metaclass=ABCMeta):
    """Delivers images to a guiding module."""

    @abstractmethod
    async def next_image(self, exposure_time: float | None, not_before: float) -> Image:
        """Return the next image to guide on.

        Args:
            exposure_time: Exposure time to use, None to leave the camera's setting alone.
            not_before: UTC unix time; the image must have started exposing at or after this.

        Returns:
            Next image.
        """
        ...

    async def reset(self) -> None:
        """Called when the guider has no reference image (start, or after a reset)."""
        pass

    async def close(self) -> None:
        """Release any resources, e.g. an open stream connection."""
        pass


class GrabDataSource(GuidingFrameSource):
    """Images via the camera's grab_data(), downloaded through the VFS. Works with every camera."""

    def __init__(self, module: Module, camera: str, broadcast: bool = False):
        """Creates a new source.

        Args:
            module: Guiding module, used for proxies, camera settings and the VFS.
            camera: Name of camera module.
            broadcast: Whether the camera should broadcast new images.
        """
        self._module = module
        self._camera = camera
        self._broadcast = broadcast

    async def next_image(self, exposure_time: float | None, not_before: float) -> Image:
        # grab_data() only returns frames started after the call, and we're called after not_before
        module = self._module

        # do camera settings
        async with module.proxy(self._camera, IData) as camera:
            await module._do_camera_settings(camera)  # type: ignore[attr-defined]

        # take image
        async with module.safe_proxy(self._camera, IExposureTime) as camera:
            if camera and exposure_time is not None:
                log.info("Taking image with an exposure time of %.2fs...", exposure_time)
                await camera.set_exposure_time(exposure_time)
            else:
                log.info("Taking image...")
        async with module.safe_proxy(self._camera, IImageType) as camera:
            if camera:
                await camera.set_image_type(ImageType.GUIDING)
        async with module.proxy(self._camera, IData) as camera:
            filename = await camera.grab_data(broadcast=self._broadcast)

        # download image
        return await module.vfs.read_image(filename)


class RawStreamSource(GuidingFrameSource):
    """Images from a BaseVideo camera's raw frame stream (/video.raw).

    Keeps one connection open and always takes the newest frame that fulfils the timing and
    exposure-time conditions. The stream only carries the camera's own headers, so FITS headers
    from other modules (telescope position, filter, focus) are requested by this source itself.
    Optionally crops the stream around the brightest star, found in a full frame whenever the
    guider has no reference image.
    """

    def __init__(
        self,
        module: Module,
        camera: str,
        path: str | None = None,
        crop_size: int | None = None,
        header_timeout: float = 10.0,
    ):
        """Creates a new source.

        Args:
            module: Guiding module, used for proxies, header requests and the VFS.
            camera: Name of camera module.
            path: VFS path of the raw stream. None asks the camera for it (IVideo capabilities).
            crop_size: Edge length in unbinned pixels of a box around the brightest star to crop
                the stream to. None for full frames.
            header_timeout: Maximum seconds to wait for FITS headers from other modules.
        """
        self._module = module
        self._camera = camera
        self._path = path
        self._crop_size = crop_size
        self._header_timeout = header_timeout
        self._crop: tuple[int, int, int, int] | None = None
        self._needs_crop = crop_size is not None
        self._exposure_time: float | None = None
        self._session: aiohttp.ClientSession | None = None
        self._response: aiohttp.ClientResponse | None = None
        self._connected_crop: tuple[int, int, int, int] | None = None

    async def next_image(self, exposure_time: float | None, not_before: float) -> Image:
        # new exposure time?
        if exposure_time is not None and exposure_time != self._exposure_time:
            async with self._module.safe_proxy(self._camera, IExposureTime) as camera:
                if camera:
                    log.info("Setting exposure time of stream to %.2fs...", exposure_time)
                    await camera.set_exposure_time(exposure_time)
            self._exposure_time = exposure_time

        # FITS headers from other modules, requested after the telescope settled; they're collected
        # while we wait for the frame
        own_name = self._module.comm.name
        exclude = {own_name} if own_name is not None else set()
        futures = await request_fits_headers(self._module, before=True, exclude=exclude)

        # need a new crop?
        if self._needs_crop:
            full_meta, full_data = await self._read_frame(None, not_before)
            self._crop = await self._find_crop(full_meta, full_data)
            self._needs_crop = False
            if self._crop is None:
                log.warning("No star found for cropping, using full frames until next reset.")
            else:
                log.info("Cropping stream to %s around brightest star.", self._crop)

        meta, data = await self._read_frame(self._crop, not_before)

        # build image
        image = Image(data)
        for key, value in meta.items():
            if key in _WIRE_KEYS or key.startswith("NAXIS") or key in ("SIMPLE", "BITPIX", "EXTEND"):
                continue
            try:
                image.header[key] = value
            except (ValueError, KeyError):
                log.debug("Skipping header %s from stream.", key)
        image.header["IMAGETYP"] = ImageType.GUIDING.value
        await add_requested_fits_headers(image, futures, self._header_timeout)
        return image

    async def reset(self) -> None:
        # find a new guide star in a full frame next time
        self._crop = None
        self._needs_crop = self._crop_size is not None

    async def close(self) -> None:
        if self._response is not None:
            self._response.close()
            self._response = None
        if self._session is not None:
            await self._session.close()
            self._session = None
        self._connected_crop = None

    async def _read_frame(
        self, crop: tuple[int, int, int, int] | None, not_before: float
    ) -> tuple[dict[str, Any], np.ndarray]:
        """Read frames from the stream until one fulfils the timing and exposure-time conditions."""
        if self._response is None or self._connected_crop != crop:
            await self._connect(crop)

        # number of frames read here that arrived after not_before, for frames without a start time
        arrived = 0
        while True:
            try:
                meta, data = await self._read_part()
            except (aiohttp.ClientError, ConnectionError, EOFError, ValueError) as e:
                await self.close()
                raise exc.GrabImageError(f"Could not read from raw stream: {e}")
            if self._arrived_after(meta, not_before):
                arrived += 1
            if self._accept(meta, not_before, arrived):
                return meta, data

    @staticmethod
    def _arrived_after(meta: dict[str, Any], not_before: float) -> bool:
        """Whether a frame arrived at the camera module at or after not_before."""
        try:
            return bool(Time(meta["DATE-ARR"]).unix >= not_before)
        except (KeyError, ValueError):
            return False

    def _accept(self, meta: dict[str, Any], not_before: float, arrived: int = 0) -> bool:
        """Whether a frame started after not_before and was taken with the requested exposure time.

        Args:
            meta: Frame meta data.
            not_before: Earliest allowed exposure start as UTC unix time.
            arrived: Number of frames (including this one) that arrived after not_before, used for
                frames without any start time.
        """
        exptime = meta.get("EXPTIME")
        if self._exposure_time is not None and exptime is not None:
            if abs(exptime - self._exposure_time) > _EXPTIME_TOLERANCE * self._exposure_time:
                return False

        # no start time at all: DATE-OBS is only the arrival time. Like BaseVideo.grab_data(), skip the
        # frame that was exposing at not_before, i.e. take the second frame arriving after it
        if meta.get("DATE-SRC") == "unknown":
            return arrived >= 2

        try:
            start = Time(meta["DATE-OBS"]).unix
        except (KeyError, ValueError):
            return True
        # an estimated start may be off by up to one frame (frames queued in the driver)
        if meta.get("DATE-SRC") == "estimated":
            start -= exptime or 0.0
        return bool(start >= not_before)

    async def _connect(self, crop: tuple[int, int, int, int] | None) -> None:
        """(Re)connect to the raw stream."""
        await self.close()

        # find stream
        path = self._path
        if path is None:
            async with self._module.proxy(self._camera, IVideo) as camera:
                capabilities = await cast(Proxy, camera).wait_for_capabilities(IVideo)
            if capabilities is None or capabilities.raw is None:
                raise exc.GrabImageError(f"Camera {self._camera} does not provide a raw stream.")
            path = capabilities.raw
        stream = self._module.vfs.open_file(path, "r")
        url, headers = stream.url, stream.headers  # type: ignore[attr-defined]

        params = {}
        if crop is not None:
            params = {"x": str(crop[0]), "y": str(crop[1]), "w": str(crop[2]), "h": str(crop[3])}

        log.info("Connecting to raw stream at %s...", url)
        self._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=None, sock_read=120))
        self._response = await self._session.get(url, headers=headers, params=params)
        if self._response.status != 200:
            status = self._response.status
            await self.close()
            raise exc.GrabImageError(f"Could not connect to raw stream, HTTP status {status}.")
        self._connected_crop = crop

    async def _read_part(self) -> tuple[dict[str, Any], np.ndarray]:
        """Read one multipart part (see BaseVideo.raw_handler()) and decode it."""
        if self._response is None:
            raise ConnectionError("Not connected.")
        content = self._response.content

        # boundary, skipping the CRLF that ends the previous part
        while True:
            line = await content.readline()
            if not line:
                raise EOFError("Stream ended.")
            if line.rstrip(b"\r\n") == _RAW_BOUNDARY:
                break

        # part headers
        meta: dict[str, Any] | None = None
        while True:
            line = await content.readline()
            if not line:
                raise EOFError("Stream ended.")
            if line in (b"\r\n", b"\n"):
                break
            name, _, value = line.decode().partition(":")
            if name.strip().lower() == "x-pyobs-frame-meta":
                meta = json.loads(value.strip())
        if meta is None:
            raise ValueError("Frame without meta header.")

        # data
        dtype = np.dtype(meta["DTYPE"])
        naxis = int(meta.get("NAXIS", 2))
        shape = tuple(int(meta[f"NAXIS{i}"]) for i in range(naxis, 0, -1))
        count = int(np.prod(shape))
        raw = await content.readexactly(count * dtype.itemsize)
        data = np.frombuffer(raw, dtype=dtype).reshape(shape)
        return meta, data

    async def _find_crop(self, meta: dict[str, Any], data: np.ndarray) -> tuple[int, int, int, int] | None:
        """Crop box around the brightest star in a full frame, or None if there's no star."""
        if self._crop_size is None:
            return None
        return await crop_around_brightest_star(data, self._crop_size)


async def crop_around_brightest_star(data: np.ndarray, size: int) -> tuple[int, int, int, int] | None:
    """Box of the given size around the brightest source in the image, clipped to the image.

    Args:
        data: Image data.
        size: Edge length of the box in pixels.

    Returns:
        (x, y, w, h) with 0-based origin, or None if no source was found.
    """
    image = await SepSourceDetection()(Image(data.astype(np.float32)))
    catalog = image.catalog
    if catalog is None or len(catalog) == 0:
        return None

    # brightest source; catalog positions follow the FITS convention (1-based)
    brightest = catalog[int(np.argmax(catalog["flux"]))]
    cx, cy = float(brightest["x"]) - 1.0, float(brightest["y"]) - 1.0

    height, width = data.shape[:2]
    w, h = min(size, width), min(size, height)
    x = int(round(min(max(cx - w / 2, 0), width - w)))
    y = int(round(min(max(cy - h / 2, 0), height - h)))
    return x, y, w, h


__all__ = ["GuidingFrameSource", "GrabDataSource", "RawStreamSource", "crop_around_brightest_star"]
