from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field, PrivateAttr

import pyobs.utils.exceptions as exc
from pyobs.interfaces import (
    IAcquisition,
    IAutoGuiding,
    IBinning,
    ICamera,
    IExposureTime,
    IFilters,
    IImageType,
    IPointingRaDec,
    ITelescope,
    IWindow,
)
from pyobs.robotic.scheduler.targets import SiderealTarget, Target
from pyobs.robotic.scripts import Script
from pyobs.robotic.utils.exptime import ExposureTimeProvider
from pyobs.utils.enums import ImageType
from pyobs.utils.parallel import Future
from pyobs.utils.time import Time

if TYPE_CHECKING:
    from pyobs.robotic.task import TaskData


log = logging.getLogger(__name__)


class AcquisitionConfig(BaseModel):
    enabled: bool = True
    optional: bool = False


class GuidingConfig(BaseModel):
    enabled: bool = True
    optional: bool = False


class InstrumentConfig(BaseModel):
    exposure_time: float | ExposureTimeProvider = 0.0
    count: int = 1
    image_type: ImageType = ImageType.OBJECT
    binning: tuple[int, int] = (1, 1)
    window: tuple[int, int, int, int] | None = None
    optical_filter: str | None = None

    async def get_exposure_time(self) -> float:
        """Return the exposure time, computing it dynamically if needed."""
        if isinstance(self.exposure_time, ExposureTimeProvider):
            return await self.exposure_time()
        return self.exposure_time


class Configuration(BaseModel):
    acquisition_config: AcquisitionConfig = Field(default_factory=AcquisitionConfig)
    guiding_config: GuidingConfig = Field(default_factory=GuidingConfig)
    instrument_configs: list[InstrumentConfig] = Field(default_factory=lambda: [InstrumentConfig()])
    repeats: int = 1


class ImagingScript(Script):
    """Default script for imaging configs."""

    configuration: Configuration = Field(default_factory=Configuration)

    camera: str
    telescope: str | None = None
    filters: str | None = None
    autoguider: str | None = None
    acquisition: str | None = None

    _object_name: str | None = PrivateAttr(default=None)

    def _image_types(self) -> list[ImageType]:
        return list({instr.image_type for instr in self.configuration.instrument_configs})

    def _optical_filters(self) -> list[str]:
        return list(
            {
                instr.optical_filter
                for instr in self.configuration.instrument_configs
                if instr.optical_filter is not None
            }
        )

    async def can_run(self, data: TaskData | None) -> bool:
        """Whether this config can currently run.

        Returns:
            True, if the script can run now
        """

        # need camera
        if not await self.comm.has_proxy(self.camera, ICamera):
            self._cant_run_reason = "No camera found."
            return False

        # for OBJECT exposure we need more
        if ImageType.OBJECT in self._image_types():
            # we need a working telescope
            async with self.comm.safe_proxy(self.telescope, ITelescope) as telescope:
                if telescope is None or not await telescope.is_ready():
                    self._cant_run_reason = "Telescope not found or not ready."
                    return False

            # we probably need filters and autoguider/acquisition
            if len(self._optical_filters()) > 0 and not await self.comm.has_proxy(self.filters, IFilters):
                self._cant_run_reason = "No filterwheel found."
                return False

            # acquisition?
            if self.configuration.acquisition_config.enabled and not await self.comm.has_proxy(
                self.acquisition, IAcquisition
            ):
                self._cant_run_reason = "No acquisition found."
                return False

            # guiding?
            if self.configuration.guiding_config.enabled and not await self.comm.has_proxy(
                self.autoguider, IAutoGuiding
            ):
                self._cant_run_reason = "No autoguider found."
                return False

        # seems alright
        self._cant_run_reason = None
        return True

    async def run(self, data: TaskData | None) -> None:
        """Run script.

        Raises:
            InterruptedError: If interrupted
        """

        # start tracking target
        track, target = await self._track_target(data)

        # acquisition?
        await self._perform_acquisition(track)

        # guiding?
        await self._start_guiding(track)

        # total (exposure) time done in this config
        self.exptime_done = 0.0

        # repeat configuration
        await self._run_configurations(target, track)

        # stop auto guiding and telescope
        await self._stop_all()

    async def _track_target(self, data: TaskData | None) -> tuple[Future | asyncio.Task[Any], Target | None]:
        # got a target?
        target = data.task.target if data is not None and data.task is not None else None
        track: Future | asyncio.Task[Any] = Future(empty=True)
        if ImageType.OBJECT in self._image_types() and target is not None:
            log.info("Moving to target %s...", target.name)
            async with self.comm.proxy(self.telescope, IPointingRaDec) as telescope:
                if isinstance(target, SiderealTarget):
                    track = asyncio.create_task(telescope.move_radec(target.ra, target.dec))
                else:
                    raise exc.MotionError("Only sidereal targets allowed.")
        return track, target

    async def _perform_acquisition(self, track: Future | asyncio.Task[Any]) -> None:
        if self.configuration.acquisition_config.enabled:
            # wait for track
            await track

            # do acquisition
            try:
                async with self.comm.proxy(self.acquisition, IAcquisition) as acquisition:
                    log.info("Performing acquisition...")
                    await acquisition.acquire_target()
            except Exception:
                if self.configuration.acquisition_config.optional:
                    log.warning("Could not acquire target, will continue without.")
                else:
                    raise

    async def _start_guiding(self, track: Future | asyncio.Task[Any]) -> None:
        if self.configuration.guiding_config.enabled:
            # wait for track
            await track

            # start auto-guiding
            async with self.comm.proxy(self.autoguider, IAutoGuiding) as autoguider:
                log.info("Starting auto-guiding...")
                await autoguider.start()

    async def _run_configurations(self, target: Target | None, track: Future | asyncio.Task[Any]) -> None:
        for repeat in range(self.configuration.repeats):
            await self._run_configuration(repeat, target, track)

    async def _run_configuration(self, repeat: int, target: Target | None, track: Future | asyncio.Task[Any]) -> None:
        log.info("Starting configuration repeat %s/%s...", repeat + 1, self.configuration.repeats)

        # loop instrument configs
        for instrument_config in self.configuration.instrument_configs:
            await self._setup_instrument_config(instrument_config, target, track)

            # do repeats
            for repeat2 in range(instrument_config.count):
                await self._expose_image(instrument_config, repeat2)

            # reset object name
            self._object_name = None

    async def _setup_instrument_config(
        self, instrument_config: InstrumentConfig, target: Target | None, track: Future | asyncio.Task[Any]
    ) -> None:
        async with self.comm.safe_proxy(self.camera, IBinning) as camera:
            if camera:
                log.info("Setting binning to %sx%s...", instrument_config.binning[0], instrument_config.binning[1])
                await camera.set_binning(*instrument_config.binning)

        async with self.comm.safe_proxy(self.camera, IWindow) as camera:
            if camera:
                wnd = instrument_config.window
                if wnd is None:
                    wnd = await camera.get_full_frame()
                log.info("Setting window to %sx%s at %s,%s...", wnd[2], wnd[3], wnd[0], wnd[1])
                await camera.set_window(*wnd)

        async with self.comm.safe_proxy(self.camera, IExposureTime) as camera:
            if camera:
                exposure_time = await instrument_config.get_exposure_time()
                log.info("Setting exposure time to %ss...", exposure_time)
                await camera.set_exposure_time(exposure_time)

        # set image type
        async with self.comm.safe_proxy(self.camera, IImageType) as camera:
            if camera:
                log.info("Setting image type to %s...", instrument_config.image_type)
                await camera.set_image_type(instrument_config.image_type)

        set_filter: Future | asyncio.Task[Any] = Future(empty=True)
        if instrument_config.optical_filter is not None:
            async with self.comm.proxy(self.filters, IFilters) as filters:
                log.info("Setting filter to %s...", instrument_config.optical_filter)
                set_filter = asyncio.create_task(filters.set_filter(instrument_config.optical_filter))

        # wait for tracking and filter
        await Future.wait_all([track, set_filter])

        # set object name?
        if instrument_config.image_type == ImageType.OBJECT and target is not None:
            self._object_name = target.name

    async def _expose_image(self, instrument_config: InstrumentConfig, repeat2: int) -> None:
        log.info("Exposing image %s/%s...", repeat2 + 1, instrument_config.count)

        # grab image
        async with self.comm.proxy(self.camera, ICamera) as camera:
            await camera.grab_data()
        self.exptime_done += await instrument_config.get_exposure_time()

    async def _stop_all(self) -> None:
        if self.autoguider is not None and self.configuration.guiding_config.enabled:
            log.info("Stopping auto-guiding...")
            async with self.comm.proxy(self.autoguider, IAutoGuiding) as autoguider:
                await autoguider.stop()

        if self.telescope is not None:
            log.info("Stopping telescope...")
            async with self.comm.proxy(self.telescope, ITelescope) as telescope:
                await telescope.stop_motion()

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

    def estimate_duration(self, data: TaskData | None = None, time: Time | None = None) -> float:
        """Estimate the duration of this script in seconds."""
        # TODO: get some good estimates for slewing/filter/acquisition etc
        duration = (
            sum(
                (ic.exposure_time if isinstance(ic.exposure_time, float) else ic.exposure_time.default_exposure_time)
                * ic.count
                for ic in self.configuration.instrument_configs
            )
            * self.configuration.repeats
            + 60.0
        )
        if self.configuration.acquisition_config.enabled:
            duration += 30.0
        return duration


__all__ = ["ImagingScript"]
