from __future__ import annotations

import asyncio
import logging
from typing import Any

import astropy.units as u
import numpy as np

import pyobs.utils.exceptions as exc
from pyobs.images.meta import OnSkyDistance
from pyobs.images.meta.exptime import ExpTime
from pyobs.interfaces import (
    AltAzOffsetState,
    AltAzState,
    IAcquisition,
    IOffsetsAltAz,
    IOffsetsRaDec,
    IPointingAltAz,
    IPointingRaDec,
    RaDecOffsetState,
    RaDecState,
)
from pyobs.mixins import CameraSettingsMixin
from pyobs.modules import Module, raises, timeout
from pyobs.utils.enums import ImageType
from pyobs.utils.publisher import CsvPublisher
from pyobs.utils.time import Time

from ...interfaces import (
    ICamera,
    IData,
    IExposureTime,
    IImageType,
    ITelescope,
)
from ._base import BasePointing

log = logging.getLogger(__name__)


class Acquisition(BasePointing, CameraSettingsMixin, IAcquisition):
    """Class for telescope acquisition."""

    __module__ = "pyobs.modules.pointing"

    def __init__(
        self,
        exposure_time: float,
        target_pixel: tuple[float, float] | None = None,
        attempts: int = 5,
        tolerance: float = 1,
        max_offset: float = 120,
        log_file: str | None = None,
        oneshot: bool = False,
        broadcast: bool = False,
        **kwargs: Any,
    ):
        """Create a new acquisition.

        Args:
            exposure_time: Default exposure time.
            target_pixel: (x, y) tuple of pixel that the star should be positioned on. If None, center of image is used.
            attempts: Number of attempts before giving up.
            tolerance: Tolerance in position to reach in arcsec.
            max_offset: Maximum offset to move in arcsec.
            log_file: Name of file to write log to.
            oneshot: For a oneshot the number of attempts is automatically set to 1 and the method finishes whether
                     successful or not.
            broadcast: Whether to broadcast acquisition images.
        """
        BasePointing.__init__(self, **kwargs)

        # store
        self._default_exposure_time = exposure_time
        self._is_running = False
        self._target_pixel = target_pixel
        self._attempts = attempts
        self._tolerance = tolerance * u.arcsec
        self._max_offset = max_offset * u.arcsec
        self._abort_event = asyncio.Event()
        self._oneshot = oneshot
        self._broadcast = broadcast

        # init log file
        self._publisher = CsvPublisher(log_file) if log_file is not None else None

        # init camera settings mixin
        CameraSettingsMixin.__init__(self, **kwargs)

    async def open(self) -> None:
        """Open module"""
        await Module.open(self)

        # check telescope and camera
        if not await self.has_proxy(self._telescope, ITelescope):
            log.warning("Telescope does not exist or is not of correct type at the moment.")
        if not await self.has_proxy(self._camera, ICamera):
            log.warning("Camera does not exist or is not of correct type at the moment.")

    async def is_running(self, **kwargs: Any) -> bool:
        """Whether a service is running."""
        return self._is_running

    @raises(exc.AbortedError, exc.AcquisitionError)
    @timeout(120)
    async def acquire_target(self, **kwargs: Any) -> dict[str, Any]:
        """Acquire target at given coordinates.

        If no RA/Dec are given, start from current position. Might not work for some implementations that require
        coordinates.

        Returns:
            A dictionary with entries for datetime, ra, dec, alt, az, and either off_ra, off_dec or off_alt, off_az.

        Raises:
            ValueError: If target could not be acquired.
        """

        try:
            self._is_running = True
            self._abort_event = asyncio.Event()
            return await self._acquire(self._default_exposure_time)
        finally:
            self._is_running = False

    async def _acquire(self, exposure_time: float) -> dict[str, Any]:
        """Actually acquire target."""

        # do camera settings
        async with self.proxy(self._camera, ICamera) as camera:
            await self._do_camera_settings(camera)
        async with self.proxy(self._camera, IImageType) as camera:
            await camera.set_image_type(ImageType.ACQUISITION)

        # try given number of attempts
        for a in range(self._attempts):
            # abort?
            if self._abort_event.is_set():
                raise exc.AbortedError()

            # set exposure time and image type and take image
            async with self.safe_proxy(self._camera, IExposureTime) as camera:
                if camera:
                    log.info("Exposing image for %.1f seconds...", exposure_time)
                    await camera.set_exposure_time(exposure_time)
                else:
                    log.info("Exposing image...")
            async with self.safe_proxy(self._camera, IData) as camera:
                if camera:
                    filename = await camera.grab_data(broadcast=self._broadcast)
                else:
                    raise exc.GeneralError("Cannot grab data from camera.")

            # download image
            log.info("Downloading image...")
            if filename is None:
                log.warning("Did not receive an image.")
                continue
            image = await self.vfs.read_image(filename)

            # get offset
            log.info("Analysing image...")
            try:
                image = await self.run_pipeline(image)
            except Exception as e:
                log.warning("Error in pipeline: %s. Skipping image.", e)
                continue

            # calculate distance from offset
            if not image.has_meta(OnSkyDistance):
                log.warning("No on-sky distance found in meta.")
                continue
                # raise exc.ImageError("No on sky distance found in meta.")
            osd = image.get_meta(OnSkyDistance)
            if osd is None or np.isnan(osd.distance):
                log.warning("On-sky distance found in meta is None or NaN.")
                continue
            log.info("Found a distance to target of %.2f arcsec.", osd.distance.arcsec)

            # get distance
            if osd.distance < self._tolerance:
                # we're finished!
                log.info("Target successfully acquired.")
                return await self._create_log_and_return()

            # abort?
            if osd.distance > self._max_offset:
                # move a maximum of 120"=2'
                raise exc.ImageError("Calculated offsets too large.")

            # apply offsets
            async with self.proxy(self._telescope, ITelescope) as telescope:
                if await self._apply(image, telescope, self._location):
                    log.info("Finished image.")
                else:
                    log.warning("Could not apply offsets.")

            if self._oneshot:
                # we're finished!
                log.info("Finishing acquisition after oneshot.")
                return await self._create_log_and_return()

            # new exposure time?
            if image.has_meta(ExpTime):
                exposure_time = image.get_meta(ExpTime).exptime

        # could not acquire target
        raise exc.AcquisitionError("Could not acquire target within given tolerance.")

    async def _create_log_and_return(self) -> dict[str, Any]:
        # get current Alt/Az
        async with self.proxy(self._telescope, IPointingAltAz) as telescope:
            altaz: AltAzState | None = telescope.get_state(IPointingAltAz)
            cur_alt, cur_az = (altaz.alt, altaz.az) if altaz is not None else (0.0, 0.0)
        async with self.proxy(self._telescope, IPointingRaDec) as telescope:
            radec: RaDecState | None = telescope.get_state(IPointingRaDec)
            cur_ra, cur_dec = (radec.ra, radec.dec) if radec is not None else (0.0, 0.0)

        # prepare log entry
        log_entry = {"datetime": Time.now().isot, "ra": cur_ra, "dec": cur_dec, "alt": cur_alt, "az": cur_az}

        # Alt/Az or RA/Dec?
        async with self.safe_proxy(self._telescope, IOffsetsRaDec) as telescope:
            if telescope:
                s: RaDecOffsetState | None = telescope.get_state(IOffsetsRaDec)
                if s is not None:
                    log_entry["off_ra"], log_entry["off_dec"] = s.ra, s.dec
        async with self.safe_proxy(self._telescope, IOffsetsAltAz) as telescope:
            if telescope:
                s2: AltAzOffsetState | None = telescope.get_state(IOffsetsAltAz)
                if s2 is not None:
                    log_entry["off_alt"], log_entry["off_az"] = s2.alt, s2.az

        # write log
        if self._publisher is not None:
            await self._publisher(**log_entry)

        # finished
        return log_entry

    async def abort(self, **kwargs: Any) -> None:
        """Abort current actions."""
        self._abort_event.set()


__all__ = ["Acquisition"]
