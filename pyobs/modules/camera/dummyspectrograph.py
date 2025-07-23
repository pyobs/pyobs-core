import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Any
import numpy as np
from astropy.io import fits

from pyobs.modules.camera.basespectrograph import BaseSpectrograph
from pyobs.utils.enums import ExposureStatus


log = logging.getLogger(__name__)


class DummySpectrograph(BaseSpectrograph):
    """A dummy spectrograph for testing."""

    __module__ = "pyobs.modules.camera"

    def __init__(self, **kwargs: Any):
        """Creates a new dummy cammera.

        Args:
            readout_time: Readout time in seconds.
            sim: Dictionary with config for image simulator.
        """
        BaseSpectrograph.__init__(self, **kwargs)

    async def _expose(self, abort_event: asyncio.Event) -> fits.HDUList:
        """Actually do the exposure, should be implemented by derived classes.

        Args:
            abort_event: Event that gets triggered when exposure should be aborted.

        Returns:
            The actual image and, if present, a filename.

        Raises:
            ValueError: If exposure was not successful.
        """

        # do exposure
        log.info("Starting exposure...")
        exposure_time = 1.0
        date_obs = datetime.now(timezone.utc)
        self._exposing = True
        steps = 10
        for i in range(steps):
            if abort_event.is_set() or not self._exposing:
                self._exposing = False
                await self._change_exposure_status(ExposureStatus.IDLE)
                raise ValueError("Exposure was aborted.")
            time.sleep(exposure_time / steps)
        self._exposing = False

        # readout
        await self._change_exposure_status(ExposureStatus.READOUT)
        time.sleep(1)

        # get data
        x = np.arange(5000, 8000, 1)
        y = np.sin(x)

        # get spectrum
        hdu = fits.PrimaryHDU(y)

        # add headers
        hdu.header["DATE-OBS"] = date_obs.strftime("%Y-%m-%dT%H:%M:%S.%f")
        hdu.header["CRVAL1"] = 5000
        hdu.header["CDELT1"] = 1

        # finished
        log.info("Exposure finished.")
        return fits.HDUList([hdu])

    def _abort_exposure(self) -> None:
        """Abort the running exposure. Should be implemented by derived class.

        Returns:
            Success or not.
        """
        self._exposing = False

    async def get_exposure_progress(self, **kwargs: Any) -> float:
        """Returns the progress of the current exposure in percent.

        Returns:
            Progress of the current exposure in percent.
        """
        return 1.0


__all__ = ["DummySpectrograph"]
