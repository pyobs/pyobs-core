from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr

import pyobs.utils.exceptions as exc
from pyobs.interfaces import (
    FitsHeaderEntry,
    IAcquisition,
    IAutoGuiding,
    IBinning,
    ICamera,
    IDome,
    IExposureTime,
    IFilters,
    IImageType,
    IPointingRaDec,
    IReady,
    IRoof,
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
    from pyobs.robotic.instruments import CameraCapability
    from pyobs.robotic.task import TaskData


log = logging.getLogger(__name__)


class AcquisitionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = Field(
        default=True, description="Whether to perform acquisition before starting this configuration."
    )
    optional: bool = Field(
        default=False, description="If acquisition fails, continue without it instead of aborting the script."
    )


class GuidingConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = Field(default=True, description="Whether to start auto-guiding before starting this configuration.")
    optional: bool = Field(
        default=False, description="If starting auto-guiding fails, continue without it instead of aborting the script."
    )


class InstrumentConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    exposure_time: float | ExposureTimeProvider = Field(
        default=0.0, description="Exposure time in seconds, or a provider that computes it dynamically."
    )
    count: int = Field(default=1, description="Number of exposures to take with this configuration.")
    image_type: ImageType = Field(
        default=ImageType.OBJECT,
        description="Type of image to take: OBJECT (science), BIAS, DARK, SKYFLAT, FOCUS, ACQUISITION, or GUIDING.",
    )
    binning: tuple[int, int] = Field(default=(1, 1), description="Detector binning as (x, y).")
    window: tuple[int, int, int, int] | None = Field(
        default=None,
        description="Detector sub-window as (left, top, width, height). Uses the full frame if unset.",
    )
    optical_filter: str | None = Field(
        default=None, description="Name of the filter to use. Uses the camera's current filter if unset."
    )

    async def get_exposure_time(self) -> float:
        """Return the exposure time, computing it dynamically if needed."""
        if isinstance(self.exposure_time, ExposureTimeProvider):
            return await self.exposure_time()
        return self.exposure_time


class Configuration(BaseModel):
    model_config = ConfigDict(extra="forbid")

    acquisition_config: AcquisitionConfig = Field(
        default_factory=AcquisitionConfig, description="Settings for acquiring the target before exposing."
    )
    guiding_config: GuidingConfig = Field(
        default_factory=GuidingConfig, description="Settings for auto-guiding while exposing."
    )
    instrument_configs: list[InstrumentConfig] = Field(
        default_factory=lambda: [InstrumentConfig()],
        description="Sequence of instrument configurations to run, in order, once per repeat.",
    )
    repeats: int = Field(
        default=1, description="Number of times to repeat the full sequence of instrument configurations."
    )


class ImagingScript(Script):
    """Default script for imaging configs."""

    configuration: Configuration = Field(default_factory=Configuration, description="What to expose and how.")

    camera: Annotated[str, ICamera, IBinning, IWindow, IExposureTime, IImageType] = Field(
        description="Name of the camera module to expose with."
    )
    telescope: Annotated[str | None, ITelescope, IPointingRaDec] = Field(
        default=None, description="Name of the telescope module to point at the target. Required for OBJECT exposures."
    )
    dome: Annotated[str | None, IDome] = Field(
        default=None, description="Name of the dome module, if the site has a rotating dome (omit for a plain roof)."
    )
    roof: Annotated[str | None, IRoof] = Field(
        default=None, description="Name of the roof module, if the site has a plain open/close roof (omit for a dome)."
    )
    filters: Annotated[str | None, IFilters] = Field(
        default=None, description="Name of the filter wheel module. Required if any instrument config sets a filter."
    )
    autoguider: Annotated[str | None, IAutoGuiding] = Field(
        default=None, description="Name of the auto-guiding module. Required if guiding is enabled."
    )
    acquisition: Annotated[str | None, IAcquisition] = Field(
        default=None, description="Name of the acquisition module. Required if acquisition is enabled."
    )

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

    def _filter_change_count(self) -> int:
        """Number of times the optical filter actually changes across the full sequence
        (instrument_configs repeated `repeats` times, back-to-back). A config with no
        optical_filter set (use the camera's current filter) never counts as a change, since
        there's no way to know whether that's actually a different filter."""
        filters = [ic.optical_filter for ic in self.configuration.instrument_configs] * self.configuration.repeats
        return sum(1 for a, b in zip(filters, filters[1:]) if a is not None and b is not None and a != b)

    @staticmethod
    def _readout_time_s(camera: CameraCapability | None, instrument_config: InstrumentConfig) -> float:
        if camera is None:
            return 0.0
        x, y = instrument_config.binning
        for binning in camera.binnings:
            if binning.x == x and binning.y == y and binning.readout_time_s is not None:
                return binning.readout_time_s
        return 0.0

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
                tel_ready = telescope.get_state(IReady) if telescope is not None else None
                if telescope is None or tel_ready is None or not tel_ready.ready:
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
        target = data.resolved_target if data is not None and data.task is not None else None
        track: Future | asyncio.Task[Any] = Future(empty=True)
        if ImageType.OBJECT in self._image_types() and target is not None:
            log.info("Moving to target %s...", target.name)
            if isinstance(target, SiderealTarget):
                track = asyncio.create_task(self._start_move_radec(target.ra, target.dec))
            else:
                raise exc.MotionError("Only sidereal targets allowed.")
        return track, target

    async def _start_move_radec(self, ra: float, dec: float) -> None:
        async with self.comm.proxy(self.telescope, IPointingRaDec) as telescope:
            await telescope.move_radec(ra, dec)

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
                    cap = camera.get_capabilities(IWindow)
                    wnd = (
                        (cap.full_frame_x, cap.full_frame_y, cap.full_frame_width, cap.full_frame_height)
                        if cap is not None
                        else None
                    )
                if wnd is not None:
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

    def get_fits_headers(self, namespaces: list[str] | None = None) -> dict[str, FitsHeaderEntry]:
        """Returns FITS header for the current status of this module.

        Args:
            namespaces: If given, only return FITS headers for the given namespaces.

        Returns:
            Dictionary containing FITS headers.
        """

        # init header
        hdr: dict[str, FitsHeaderEntry] = {}

        # which image type?
        if self._object_name is not None:
            # add object name
            hdr["OBJECT"] = FitsHeaderEntry(self._object_name, "Name of target")

        # return
        return hdr

    def estimate_duration(self, data: TaskData | None = None, time: Time | None = None) -> float:
        """Estimate the duration of this script in seconds.

        Uses real per-binning readout time, per-wheel filter-change time, and telescope slew /
        dome rotate / roof open-close time wherever `data.instrument_capabilities` has a matching,
        populated row -- falling back to today's flat fudge constants at every point that's
        missing (no `data`, no capabilities, no matching module, or the specific field not set on
        the matched row). Telescope and dome/roof move in parallel, so the slew/rotate/roof term
        is the slowest of the three, not their sum.

        Two simplifications carried over from today's flat constants, not new: the slew term is
        added unconditionally, even for a bias/dark-only sequence that never actually points at
        anything; and each actual filter transition costs one flat `filter_change_time_s`
        (the portal's own one-position-step estimate) regardless of how many wheel positions
        that particular change actually spans.
        """
        capabilities = data.instrument_capabilities if data is not None else None
        camera = capabilities.camera(self.camera) if capabilities is not None else None

        duration = (
            sum(
                (
                    (
                        ic.exposure_time
                        if isinstance(ic.exposure_time, float)
                        else ic.exposure_time.default_exposure_time
                    )
                    + self._readout_time_s(camera, ic)
                )
                * ic.count
                for ic in self.configuration.instrument_configs
            )
            * self.configuration.repeats
        )

        telescope = capabilities.telescope(self.telescope) if capabilities is not None and self.telescope else None
        slew_time = telescope.estimate_slew_time_s() if telescope is not None else None
        dome = capabilities.dome(self.dome) if capabilities is not None and self.dome else None
        rotate_time = dome.estimate_rotate_time_s() if dome is not None else None
        roof = capabilities.roof(self.roof) if capabilities is not None and self.roof else None
        roof_time = roof.open_close_time_s if roof is not None else None
        times = [t for t in (slew_time, rotate_time, roof_time) if t is not None]
        duration += max(times) if times else 60.0

        if self.configuration.acquisition_config.enabled:
            duration += 30.0

        filter_wheel = capabilities.filter_wheel(self.filters) if capabilities is not None and self.filters else None
        if filter_wheel is not None and filter_wheel.filter_change_time_s is not None:
            duration += filter_wheel.filter_change_time_s * self._filter_change_count()

        return duration


__all__ = ["ImagingScript"]
