import asyncio
import logging
from pydantic import model_validator, PrivateAttr
from typing import Any, cast, Literal, Self

from pyobs.interfaces import (
    IRoof,
    IAutoGuiding,
    ITelescope,
    IAcquisition,
    ICamera,
    IFilters,
    IPointingRaDec,
)
from pyobs.robotic.scripts import Script
from pyobs.robotic.task import TaskData
from pyobs.utils.enums import ImageType
import pyobs.utils.exceptions as exc
from pyobs.utils.logger import DuplicateFilter
from pyobs.utils.parallel import Future

log = logging.getLogger(__name__)

# logger for logging name of task
cannot_run_logger = logging.getLogger(__name__ + ":cannot_run")
cannot_run_logger.addFilter(DuplicateFilter())


class DefaultScript(Script):
    """Default script for imaging configs."""

    image_type: Literal["BIAS", "DARK", "OBJECT"] = "OBJECT"

    camera: str
    roof: str | None = None
    telescope: str | None = None
    filters: str | None = None
    autoguider: str | None = None
    acquisition: str | None = None

    _image_type: ImageType = PrivateAttr()
    _roof: IRoof | None = PrivateAttr()
    _telescope: ITelescope | None = PrivateAttr()
    _camera: ICamera | None = PrivateAttr()
    _filters: IFilters | None = PrivateAttr()
    _autoguider: IAutoGuiding | None = PrivateAttr()
    _acquisition: IAcquisition | None = PrivateAttr()

    @model_validator(mode="after")
    def set_image_type(self) -> Self:
        if self.image_type == "BIAS":
            self._image_type = ImageType.BIAS
        elif self.image_type == "DARK":
            self._image_type = ImageType.DARK
        else:
            self._image_type = ImageType.OBJECT
        return self

    @model_validator(mode="after")
    async def _get_proxies(self) -> Self:
        self._roof = await self.comm.safe_proxy(self.roof, IRoof)
        self._telescope = await self.comm.safe_proxy(self.telescope, ITelescope)
        self._camera = await self.comm.safe_proxy(self.camera, ICamera)
        self._filters = await self.comm.safe_proxy(self.filters, IFilters)
        self._autoguider = await self.comm.safe_proxy(self.autoguider, IAutoGuiding)
        self._acquisition = await self.comm.safe_proxy(self.acquisition, IAcquisition)

    async def can_run(self, data: TaskData | None) -> bool:
        """Whether this config can currently run.

        Returns:
            True, if the script can run now
        """

        # need camera
        if self._camera is None:
            cannot_run_logger.info("Cannot run task, no camera found.")
            return False

        # for OBJECT exposure we need more
        if self._image_type == ImageType.OBJECT:
            # we need an open roof and a working telescope
            if self._roof is None or not await self._roof.is_ready():
                cannot_run_logger.warning("Cannot run task, no roof found or roof not ready.")
                return False
            if self._telescope is None or not await self._telescope.is_ready():
                cannot_run_logger.warning("Cannot run task, no telescope found or telescope not ready.")
                return False

            # we probably need filters and autoguider/acquisition
            if self._filters is None:
                cannot_run_logger.warning("Cannot run task, No filter module found.")
                return False

            """
            # acquisition?
            cfg = self.request.configurations[0]
            if cfg.acquisition_config is not None and cfg.acquisition_config.mode == "ON" and acquisition is None:
                cannot_run_logger.warning("Cannot run task, no acquisition found.")
                return False

            # guiding?
            if cfg.guiding_config is not None and cfg.guiding_config.mode == "ON" and autoguider is None:
                cannot_run_logger.warning("Cannot run task, no auto guider found.")
                return False
            """

        # seems alright
        return True

    async def run(self, data: TaskData | None) -> None:
        """Run script.

        Raises:
            InterruptedError: If interrupted
        """

        # got a target?
        track: Future | asyncio.Task[Any] = Future(empty=True)
        if self._image_type == ImageType.OBJECT:
            if self._telescope is None:
                raise ValueError("No telescope given.")
            log.info("Moving to target %s...", data.task.target.name)
            if isinstance(self._telescope, IPointingRaDec):
                track = asyncio.create_task(self._telescope.move_radec(data.task.target.ra, data.task.target.dec))
            else:
                raise exc.MotionError("Telescope can't move to RA/Dec.")

        """
        # acquisition?
        if cfg.acquisition_config is not None and cfg.acquisition_config.mode == "ON":
            # wait for track
            await track

            # do acquisition
            if acquisition is None:
                raise ValueError("No acquisition given.")
            log.info("Performing acquisition...")
            await acquisition.acquire_target()

        # guiding?
        if cfg.guiding_config is not None and cfg.guiding_config.mode == "ON":
            if autoguider is None:
                raise ValueError("No autoguider given.")
            log.info("Starting auto-guiding...")
            await autoguider.start()
        """

        # total (exposure) time done in this config
        self.exptime_done = 0.0

        # finally, stop telescope
        if self._image_type == ImageType.OBJECT:
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
        if self._image_type == ImageType.OBJECT:
            # add object name
            # hdr["OBJECT"] = self.request.configurations[0].target.name, "Name of target"
            pass

        # return
        return hdr


__all__ = ["DefaultScript"]
