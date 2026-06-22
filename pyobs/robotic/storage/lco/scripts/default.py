import asyncio
import logging
import time
from typing import Any

import numpy as np

from pyobs.interfaces import (
    IAcquisition,
    IAutoGuiding,
    IBinning,
    ICamera,
    IExposureTime,
    IFilters,
    IImageType,
    IPointingRaDec,
    IRoof,
    ITelescope,
    IWindow,
)
from pyobs.robotic.task import TaskData
from pyobs.utils.enums import ImageType
from pyobs.utils.logger import DuplicateFilter
from pyobs.utils.parallel import Future

from .script import LcoScript

log = logging.getLogger(__name__)

# logger for logging name of task
cannot_run_logger = logging.getLogger(__name__ + ":cannot_run")
cannot_run_logger.addFilter(DuplicateFilter())


class LcoDefaultScript(LcoScript):
    """Default script for LCO configs."""

    camera: str
    roof: str | None = None
    telescope: str | None = None
    filters: str | None = None
    autoguider: str | None = None
    acquisition: str | None = None

    @property
    def _image_type(self) -> ImageType:
        if self.request.configurations[0].type == "BIAS":
            return ImageType.BIAS
        elif self.request.configurations[0].type == "DARK":
            return ImageType.DARK
        return ImageType.OBJECT

    async def can_run(self, data: TaskData | None) -> bool:
        """Whether this config can currently run.

        Returns:
            True, if the script can run now
        """

        # need camera
        if not await self.comm.has_proxy(self.camera, ICamera):
            cannot_run_logger.info("Cannot run task, no camera found.")
            return False

        # for OBJECT exposure we need more
        if self._image_type == ImageType.OBJECT:
            # we need an open roof and a working telescope
            async with self.comm.proxy(self.roof, IRoof) as roof:
                if roof is None or not await roof.is_ready():
                    cannot_run_logger.info("Cannot run task, no roof found or roof not ready.")
                    return False
            async with self.comm.proxy(self.telescope, ITelescope) as telescope:
                if telescope is None or not await telescope.is_ready():
                    cannot_run_logger.warning("Cannot run task, no telescope found or telescope not ready.")
                    return False

            # we probably need filters and autoguider/acquisition
            if not await self.comm.has_proxy(self.filters, IFilters):
                cannot_run_logger.warning("Cannot run task, No filter module found.")
                return False

            # acquisition?
            cfg = self.request.configurations[0]
            if (
                cfg.acquisition_config is not None
                and cfg.acquisition_config.mode == "ON"
                and not await self.comm.has_proxy(self.acquisition, IAcquisition)
            ):
                cannot_run_logger.warning("Cannot run task, no acquisition found.")
                return False

            # guiding?
            if (
                cfg.guiding_config is not None
                and cfg.guiding_config.mode == "ON"
                and not await self.comm.has_proxy(self.autoguider, IAutoGuiding)
            ):
                cannot_run_logger.warning("Cannot run task, no auto guider found.")
                return False

        # seems alright
        return True

    async def run(self, data: TaskData | None) -> None:
        """Run script.

        Raises:
            InterruptedError: If interrupted
        """

        # got a target?
        cfg = self.request.configurations[0]
        track: Future | asyncio.Task[Any] = Future(empty=True)
        if self._image_type == ImageType.OBJECT:
            log.info("Moving to target %s...", cfg.target.name)
            async with self.comm.proxy(self.telescope, IPointingRaDec) as telescope:
                track = asyncio.create_task(telescope.move_radec(cfg.target.ra, cfg.target.dec))

        # acquisition?
        if cfg.acquisition_config is not None and cfg.acquisition_config.mode == "ON":
            # wait for track
            await track

            # do acquisition
            async with self.comm.proxy(self.acquisition, IAcquisition) as acquisition:
                log.info("Performing acquisition...")
                await acquisition.acquire_target()

        # guiding?
        if cfg.guiding_config is not None and cfg.guiding_config.mode == "ON":
            async with self.comm.proxy(self.autoguider, IAutoGuiding) as autoguider:
                log.info("Starting auto-guiding...")
                await autoguider.start()

        # total (exposure) time done in this config
        self.exptime_done = 0.0

        # task archive must be LCO
        from pyobs.robotic.storage.lco import LcoObservationArchive

        if data is None or not isinstance(data.observation_archive, LcoObservationArchive):
            raise ValueError("Task schedule is not for LCO observation portal.")

        # get instrument info
        # instrument_type = self.configuration["instrument_type"].lower()
        # instrument = task_schedule.instruments[instrument_type]

        # setting repeat duration depending on config type
        repeat_duration = None
        if cfg.type == "REPEAT_EXPOSE":
            if cfg.repeat_duration is not None:
                log.info("Repeating all instrument configurations for %d seconds.", cfg.repeat_duration)
            else:
                log.error("Type is REPEAT_EXPOSE, but no repeat_duration was set.")

        # config iterations
        config_finished = False
        ic_durations = []
        image_no = 1
        while not config_finished:
            # ic start time
            ic_start_time = time.time()

            # loop instrument configs
            for ic in cfg.instrument_configs:
                log.info('Using readout mode "%s"...', ic.mode)

                # set filter
                set_filter: Future | asyncio.Task[Any] = Future(empty=True)
                if (
                    ic.optical_elements is not None
                    and "filter" in ic.optical_elements
                    and await self.comm.has_proxy(self.filters, IFilters)
                ):
                    log.info("Setting filter to %s...", ic.optical_elements["filter"])
                    async with self.comm.proxy(self.filters, IFilters) as filters:
                        set_filter = asyncio.create_task(filters.set_filter(ic.optical_elements["filter"]))

                # wait for tracking and filter
                await Future.wait_all([track, set_filter])

                # set binning and window
                async with self.comm.safe_proxy(self.camera, IBinning) as camera:
                    if camera:
                        binning = ic.extra_params["binning"]
                        log.info("Set binning to %dx%d...", binning, binning)
                        await camera.set_binning(binning, binning)
                async with self.comm.safe_proxy(self.camera, IWindow) as camera:
                    if camera:
                        full_frame = await camera.get_full_frame()
                        await camera.set_window(*full_frame)

                # loop images
                for exp in range(ic.exposure_count):
                    # prepare log entry
                    # add total image number and number within IC
                    msg = f"Exposing {cfg.type} image #{image_no} ({exp + 1}/{ic.exposure_count})"

                    # set exposure time
                    async with self.comm.safe_proxy(self.camera, IExposureTime) as camera:
                        if camera is not None:
                            await camera.set_exposure_time(ic.exposure_time)
                            msg += f" for {ic.exposure_time:2f}s"

                    # set image type
                    async with self.comm.safe_proxy(self.camera, IImageType) as camera:
                        if camera is not None:
                            await camera.set_image_type(self._image_type)

                    # log it
                    log.info("%s...", msg)

                    # grab image
                    async with self.comm.proxy(self.camera, ICamera) as camera:
                        await camera.grab_data()
                    self.exptime_done += ic.exposure_time
                    image_no += 1

            # store duration for all ICs
            ic_durations.append(time.time() - ic_start_time)

            # need repeat?
            if repeat_duration is None:
                # if there is no repeat duration, we're finished
                config_finished = True

            else:
                # get average IC duration
                avg_ic_duration = np.mean(ic_durations)

                # can we do another one, i.e. is done time plus average time larger than repeat_duration?
                if sum(ic_durations) + avg_ic_duration > repeat_duration:
                    # doesn't seem so
                    config_finished = True

        # stop auto guiding
        if cfg.guiding_config is not None and cfg.guiding_config.mode == "ON" and autoguider is not None:
            log.info("Stopping auto-guiding...")
            await autoguider.stop()

        # finally, stop telescope
        if self._image_type == ImageType.OBJECT:
            async with self.comm.proxy(self.telescope, ITelescope) as telescope:
                log.info("Stopping telescope...")
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
        if self._image_type == ImageType.OBJECT:
            # add object name
            hdr["OBJECT"] = self.request.configurations[0].target.name, "Name of target"

        # return
        return hdr


__all__ = ["LcoDefaultScript"]
