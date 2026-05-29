import asyncio
import logging
from pydantic import PrivateAttr, BaseModel, Field
from typing import Any, cast

from pyobs.interfaces import (
    IAutoGuiding,
    ITelescope,
    IAcquisition,
    ICamera,
    IFilters,
    IPointingRaDec,
    IBinning,
    IWindow,
    IExposureTime,
    IImageType,
)
from pyobs.robotic.scheduler.targets import SiderealTarget
from pyobs.robotic.scripts import Script
from pyobs.robotic.task import TaskData
from pyobs.utils.enums import ImageType, MotionStatus
import pyobs.utils.exceptions as exc
from pyobs.utils.logger import DuplicateFilter
from pyobs.utils.parallel import Future

log = logging.getLogger(__name__)

# logger for logging name of task
cannot_run_logger = logging.getLogger(__name__ + ":cannot_run")
cannot_run_logger.addFilter(DuplicateFilter())


class AcquisitionConfig(BaseModel):
    enabled: bool = True
    optional: bool = False


class GuidingConfig(BaseModel):
    enabled: bool = True
    optional: bool = False


class InstrumentConfig(BaseModel):
    exposure_time: float
    count: int = 1
    image_type: ImageType = ImageType.OBJECT
    binning: tuple[int, int] = (1, 1)
    window: tuple[int, int, int, int] | None = None
    optical_filter: str | None = None


class Configuration(BaseModel):
    acquisition_config: AcquisitionConfig = Field(default_factory=AcquisitionConfig)
    guiding_config: GuidingConfig = Field(default_factory=GuidingConfig)
    instrument_configs: list[InstrumentConfig] = Field(default_factory=list)
    repeats: int = 1


class ImagingScript(Script):
    """Default script for imaging configs."""

    configuration: Configuration

    camera: str
    telescope: str | None = None
    filters: str | None = None
    autoguider: str | None = None
    acquisition: str | None = None

    _telescope: ITelescope | None = PrivateAttr(default=None)
    _camera: ICamera | None = PrivateAttr(default=None)
    _filters: IFilters | None = PrivateAttr(default=None)
    _autoguider: IAutoGuiding | None = PrivateAttr(default=None)
    _acquisition: IAcquisition | None = PrivateAttr(default=None)

    _object_name: str | None = PrivateAttr(default=None)

    async def _get_proxies(self) -> None:
        self._telescope = await self.comm.safe_proxy(self.telescope, ITelescope)
        self._camera = await self.comm.safe_proxy(self.camera, ICamera)
        self._filters = await self.comm.safe_proxy(self.filters, IFilters)
        self._autoguider = await self.comm.safe_proxy(self.autoguider, IAutoGuiding)
        self._acquisition = await self.comm.safe_proxy(self.acquisition, IAcquisition)

    def _image_types(self) -> list[ImageType]:
        return list(set([instr.image_type for instr in self.configuration.instrument_configs]))

    def _optical_filters(self) -> list[str]:
        return list(
            set(
                [
                    instr.optical_filter
                    for instr in self.configuration.instrument_configs
                    if instr.optical_filter is not None
                ]
            )
        )

    async def can_run(self, data: TaskData | None) -> bool:
        """Whether this config can currently run.

        Returns:
            True, if the script can run now
        """
        await self._get_proxies()

        # need camera
        if self._camera is None:
            cannot_run_logger.info("Cannot run task, no camera found.")
            return False

        # for OBJECT exposure we need more
        if ImageType.OBJECT in self._image_types():
            # we need a working telescope
            if self._telescope is None or not await self._telescope.is_ready():
                cannot_run_logger.warning("Cannot run task, no telescope found or telescope not ready.")
                return False

            # we probably need filters and autoguider/acquisition
            if len(self._optical_filters()) > 0 and self._filters is None:
                cannot_run_logger.warning("Cannot run task, No filter module found.")
                return False

            # acquisition?
            if self.configuration.acquisition_config.enabled and self._acquisition is None:
                cannot_run_logger.warning("Cannot run task, no acquisition found.")
                return False

            # guiding?
            if self.configuration.guiding_config.enabled and self._autoguider is None:
                cannot_run_logger.warning("Cannot run task, no auto guider found.")
                return False

        # seems alright
        return True

    async def run(self, data: TaskData | None) -> None:
        """Run script.

        Raises:
            InterruptedError: If interrupted
        """
        if self._camera is None:
            await self._get_proxies()

        # got a target?
        target = data.task.target if data is not None and data.task is not None else None
        track: Future | asyncio.Task[Any] = Future(empty=True)
        if ImageType.OBJECT in self._image_types() and target is not None:
            if self._telescope is None:
                raise ValueError("No telescope given.")
            log.info("Moving to target %s...", target.name)
            if isinstance(self._telescope, IPointingRaDec):
                if isinstance(target, SiderealTarget):
                    track = asyncio.create_task(self._telescope.move_radec(target.ra, target.dec))
                else:
                    raise exc.MotionError("Only sidereal targets allowed.")
            else:
                raise exc.MotionError("Telescope can't move to RA/Dec.")

        # acquisition?
        if self.configuration.acquisition_config.enabled:
            if self._acquisition is None:
                raise ValueError("No acquisition given.")

            # wait for track
            await track

            # do acquisition
            log.info("Performing acquisition...")
            try:
                await self._acquisition.acquire_target()
            except:
                if self.configuration.acquisition_config.optional:
                    log.warning("Could not acquire target, will continue without.")
                else:
                    raise

        # guiding?
        if self.configuration.guiding_config.enabled:
            if self._autoguider is None:
                raise ValueError("No autoguider given.")

            # wait for track
            await track

            # start auto-guiding
            log.info("Starting auto-guiding...")
            await self._autoguider.start()

        # total (exposure) time done in this config
        self.exptime_done = 0.0

        # repeat configuration
        for repeat in range(self.configuration.repeats):
            log.info(f"Starting configuration repeat {repeat+1}/{self.configuration.repeats}...")

            # loop instrument configs
            for instrument_config in self.configuration.instrument_configs:
                if isinstance(self._camera, IBinning):
                    log.info(f"Setting binning to {instrument_config.binning[0]}x{instrument_config.binning[1]}...")
                    await self._camera.set_binning(*instrument_config.binning)

                if isinstance(self._camera, IWindow):
                    wnd = instrument_config.window
                    if wnd is None:
                        wnd = await self._camera.get_full_frame()
                    log.info(f"Setting window to {wnd[2]}x{wnd[3]} at {wnd[0]},{wnd[1]}...")
                    await self._camera.set_window(*wnd)

                if isinstance(self._camera, IExposureTime):
                    log.info(f"Setting exposure time to {instrument_config.exposure_time}s...")
                    await self._camera.set_exposure_time(instrument_config.exposure_time)

                # set image type
                if isinstance(self._camera, IImageType):
                    log.info(f"Setting image type to {instrument_config.image_type}...")
                    await self._camera.set_image_type(instrument_config.image_type)

                set_filter: Future | asyncio.Task[Any] = Future(empty=True)
                if instrument_config.optical_filter is not None and self._filters is not None:
                    log.info(f"Setting filter to {instrument_config.optical_filter}...")
                    set_filter = asyncio.create_task(self._filters.set_filter(instrument_config.optical_filter))

                # wait for tracking and filter
                await Future.wait_all([track, set_filter])

                # set object name?
                if instrument_config.image_type == ImageType.OBJECT and target is not None:
                    self._object_name = target.name

                # do repeats
                for repeat2 in range(instrument_config.count):
                    log.info(f"Exposing image {repeat2+1}/{instrument_config.count}...")

                    # grab image
                    await cast(ICamera, self._camera).grab_data()
                    self.exptime_done += instrument_config.exposure_time

                # reset object name
                self._object_name = None

        # stop auto guiding
        if self._autoguider is not None and self.configuration.guiding_config.enabled:
            log.info("Stopping auto-guiding...")
            await self._autoguider.stop()

        # finally, stop telescope
        if (
            self._telescope is not None
            and await cast(ITelescope, self._telescope).get_motion_status() != MotionStatus.IDLE
        ):
            log.info("Stopping telescope...")
            await cast(ITelescope, self._telescope).stop_motion()

    def get_fits_headers(self, namespaces: list[str] | None = None) -> dict[str, Any]:
        """Returns FITS header for the current status of this module.

        Args:
            namespaces: If given, only return FITS headers for the given namespaces.

        Returns:
            Dictionary containing FITS headers.
        """

        # init header
        hdr = {}

        # which image type?
        if self._object_name is not None:
            # add object name
            hdr["OBJECT"] = self._object_name, "Name of target"

        # return
        return hdr


__all__ = ["ImagingScript"]
