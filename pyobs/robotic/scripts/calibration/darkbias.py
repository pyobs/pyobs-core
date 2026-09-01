from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Annotated, Self

from pydantic import Field, model_validator

from pyobs.interfaces import (
    IBinning,
    IData,
    IExposureTime,
    IImageType,
    IWindow,
)
from pyobs.robotic.scripts import Script
from pyobs.robotic.utils.archive import Archive
from pyobs.robotic.utils.calibration import science_exptimes_for_night
from pyobs.utils.enums import ImageType
from pyobs.utils.time import Time

if TYPE_CHECKING:
    from pyobs.robotic.task import TaskData

log = logging.getLogger(__name__)


class DarkBiasScript(Script):
    """Script for running darks or biases."""

    camera: Annotated[str, IData, IBinning, IWindow, IExposureTime, IImageType] = Field(
        description="Name of the camera module to expose with."
    )
    count: int = Field(default=20, description="Number of exposures to take.")
    exptime: float = Field(default=0, description="Exposure time in seconds. 0 takes a bias, anything else a dark.")
    exptimes: list[float] | None = Field(
        default=None, description="Explicit list of dark exposure times to take one series each of."
    )
    match_science_exptimes: bool = Field(
        default=False,
        description="Derive the dark exposure times from the night's science frames instead of a fixed list "
        "(requires archive and site). Mutually exclusive with exptime/exptimes.",
    )
    archive: Archive | None = Field(
        default=None, description="Archive to query for science exptimes. Required when match_science_exptimes=True."
    )
    site: str | None = Field(
        default=None, description="Site code to query the archive for. Required when match_science_exptimes=True."
    )
    night: str | None = Field(
        default=None,
        description="Night to derive science exptimes for (Archive.list_frames(night=...) format). Defaults to "
        "the night that just ended, derived from the current time.",
    )
    binning: tuple[int, int] = Field(default=(1, 1), description="Detector binning as (x, y).")

    @model_validator(mode="after")
    def _validate_exptime_mode(self) -> Self:
        modes_set = sum([self.exptimes is not None, self.match_science_exptimes])
        if modes_set > 1:
            raise ValueError("exptimes and match_science_exptimes are mutually exclusive.")
        if modes_set == 1 and self.exptime != 0:
            raise ValueError("exptime cannot be combined with exptimes or match_science_exptimes.")
        return self

    async def can_run(self, data: TaskData | None) -> bool:
        """Whether this config can currently run.
        Returns:
            True if script can run now.
        """

        # we need a camera
        if not await self.comm.has_proxy(self.camera, IData):
            self._cant_run_reason = "No camera found."
            return False

        # multi-exptime-from-science mode needs an archive, a site, and a way to resolve night
        if self.match_science_exptimes:
            if self.archive is None or self.site is None:
                self._cant_run_reason = "match_science_exptimes requires archive and site to be configured."
                return False
            if self.night is None and self._observer is None:
                self._cant_run_reason = "No observer configured to derive the night from."
                return False

        # seems alright
        self._cant_run_reason = None
        return True

    async def _resolve_exptimes(self) -> list[float]:
        """Resolves the series of exposure times to take: explicit list, derived from the
        night's science frames, or the single configured exptime (0 for a bias series)."""
        if self.exptimes is not None:
            return sorted(self.exptimes, reverse=True)

        if self.match_science_exptimes:
            if self.archive is None or self.site is None:
                raise ValueError("match_science_exptimes requires archive and site to be configured.")
            if self.night is not None:
                night = self.night
            elif self._observer is not None:
                night = Time.now().night_obs(self._observer).isoformat()
            else:
                raise ValueError("No observer configured to derive the night from.")
            by_combo = await science_exptimes_for_night(self.archive, self.site, night)
            exptimes = sorted({e for values in by_combo.values() for e in values}, reverse=True)
            if not exptimes:
                log.warning("No science exptimes found for night %s; nothing to expose.", night)
            return exptimes

        return [self.exptime]

    async def run(self, data: TaskData | None) -> None:
        """Run script.
        Raises:
            InterruptedError: If interrupted
        """

        async with self.comm.safe_proxy(self.camera, IBinning) as camera:
            if camera is not None:
                await camera.set_binning(*self.binning)

        # set full frame
        async with self.comm.safe_proxy(self.camera, IWindow) as camera:
            if camera is not None:
                cap = camera.get_capabilities(IWindow)
                if cap is not None:
                    await camera.set_window(
                        cap.full_frame_x, cap.full_frame_y, cap.full_frame_width, cap.full_frame_height
                    )

        exptimes = await self._resolve_exptimes()
        if len(exptimes) > 1:
            log.info("Resolved dark exptimes for %s: %s", self.camera, exptimes)

        image_type = ImageType.BIAS if exptimes == [0] else ImageType.DARK
        async with self.comm.proxy(self.camera, IImageType) as camera:
            await camera.set_image_type(image_type)

        for exptime in exptimes:
            async with self.comm.proxy(self.camera, IExposureTime) as camera:
                await camera.set_exposure_time(exptime)

            im_type = f"{self.count} biases" if exptime == 0 else f"{self.count} darks ({exptime} s)"
            log.info("Starting a series of %s with %s...", im_type, self.camera)
            async with self.comm.proxy(self.camera, IData) as camera:
                for _ in range(self.count):
                    await camera.grab_data()
            log.info("Finished series of %s with %s.", im_type, self.camera)

    def estimate_duration(self, data: TaskData | None = None, time: Time | None = None) -> float:
        """Estimate duration of the dark/bias series.

        For match_science_exptimes, the exptime list isn't known without an async archive
        query this sync method can't make; falls back to a single-series estimate using the
        configured exptime (0 by default) as a rough placeholder.
        """
        # TODO: get a better estimate for readout overhead
        readout = 5.0
        if self.exptimes is not None:
            return sum(self.count * (e + readout) for e in self.exptimes)
        return self.count * (self.exptime + readout)


__all__ = ["DarkBiasScript"]
