import asyncio
import logging
import numpy as np
from typing import Tuple, Dict, Any, Optional
import astropy.units as u

from pyobs.images.meta import OnSkyDistance
from pyobs.images.meta.exptime import ExpTime
from pyobs.interfaces import IAcquisition
from pyobs.modules import Module
from pyobs.mixins import CameraSettingsMixin
from pyobs.modules import timeout
from pyobs.utils.enums import ImageType
from pyobs.utils.publisher import CsvPublisher
from pyobs.utils.time import Time
import pyobs.utils.exceptions as exc
from ._base import BasePointing
from ...interfaces import IExposureTime, IImageType, ITelescope, IData, IOffsetsRaDec, IOffsetsAltAz, ICamera

log = logging.getLogger(__name__)


class Acquisition(BasePointing, CameraSettingsMixin, IAcquisition):
    """Class for telescope acquisition."""

    __module__ = "pyobs.modules.pointing"

    def __init__(
        self,
        exposure_time: float,
        target_pixel: Optional[Tuple[float, float]] = None,
        attempts: int = 5,
        tolerance: float = 1,
        max_offset: float = 120,
        log_file: Optional[str] = None,
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

        # init log file
        self._publisher = CsvPublisher(log_file) if log_file is not None else None

        # init camera settings mixin
        CameraSettingsMixin.__init__(self, **kwargs)

    async def open(self) -> None:
        """Open module"""
        await Module.open(self)

        # check telescope and camera
        try:
            await self.proxy(self._telescope, ITelescope)
            await self.proxy(self._camera, ICamera)
        except ValueError:
            log.warning("Either camera or telescope do not exist or are not of correct type at the moment.")

    async def is_running(self, **kwargs: Any) -> bool:
        """Whether a service is running."""
        return self._is_running

    @timeout(120)
    async def acquire_target(self, **kwargs: Any) -> Dict[str, Any]:
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

    async def _acquire(self, exposure_time: float) -> Dict[str, Any]:
        """Actually acquire target."""

        # get telescope
        log.info("Getting proxy for telescope...")
        telescope = await self.proxy(self._telescope, ITelescope)

        # get camera
        log.info("Getting proxy for camera...")
        camera = await self.proxy(self._camera, IData)

        # do camera settings
        await self._do_camera_settings(camera)

        # try given number of attempts
        for a in range(self._attempts):
            # abort?
            if self._abort_event.is_set():
                raise exc.AbortedError()

            # set exposure time and image type and take image
            if isinstance(camera, IExposureTime):
                log.info("Exposing image for %.1f seconds...", exposure_time)
                await camera.set_exposure_time(exposure_time)
            else:
                log.info("Exposing image...")
            if isinstance(camera, IImageType):
                await camera.set_image_type(ImageType.ACQUISITION)
            filename = await camera.grab_data()

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
                log.warning(f"Error in pipeline: {e}. Skipping image.")

            # calculate distance from offset
            if not image.has_meta(OnSkyDistance):
                raise exc.ImageError("No on sky distance found in meta.")
            osd = image.get_meta(OnSkyDistance)
            if osd is None or np.isnan(osd.distance):
                log.warning("No on sky distance found in meta.")
                continue
            log.info("Found a distance to target of %.2f arcsec.", osd.distance.arcsec)

            # get distance
            if osd.distance < self._tolerance:
                # we're finished!
                log.info("Target successfully acquired.")

                # get current Alt/Az
                cur_alt, cur_az = await telescope.get_altaz()
                cur_ra, cur_dec = await telescope.get_radec()

                # prepare log entry
                log_entry = {"datetime": Time.now().isot, "ra": cur_ra, "dec": cur_dec, "alt": cur_alt, "az": cur_az}

                # Alt/Az or RA/Dec?
                if isinstance(telescope, IOffsetsRaDec):
                    log_entry["off_ra"], log_entry["off_dec"] = await telescope.get_offsets_radec()
                elif isinstance(telescope, IOffsetsAltAz):
                    log_entry["off_alt"], log_entry["off_az"] = await telescope.get_offsets_altaz()

                # write log
                # TODO: reactivate!
                # if self._publisher is not None:
                #    await self._publisher(**log_entry)

                # finished
                return log_entry

            # abort?
            if osd.distance > self._max_offset:
                # move a maximum of 120"=2'
                raise exc.ImageError("Calculated offsets too large.")

            # apply offsets
            if await self._apply(image, telescope, self.location):
                log.info("Finished image.")
            else:
                log.warning("Could not apply offsets.")

            # new exposure time?
            if image.has_meta(ExpTime):
                exposure_time = image.get_meta(ExpTime).exptime

        # could not acquire target
        raise exc.ImageError("Could not acquire target within given tolerance.")

    async def abort(self, **kwargs: Any) -> None:
        """Abort current actions."""
        self._abort_event.set()


__all__ = ["Acquisition"]
