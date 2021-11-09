import logging
import threading
import time
from datetime import datetime
from typing import Dict, Any, Optional, TYPE_CHECKING, Tuple
import numpy as np
from astropy.io import fits

from pyobs.modules.camera.basespectrograph import BaseSpectrograph
from pyobs.utils.enums import ExposureStatus
if TYPE_CHECKING:
    from pyobs.utils.simulation import SimWorld


log = logging.getLogger(__name__)


class DummySpectrograph(BaseSpectrograph):
    """A dummy spectrograph for testing."""
    __module__ = 'pyobs.modules.camera'

    def __init__(self, **kwargs: Any):
        """Creates a new dummy cammera.

        Args:
            readout_time: Readout time in seconds.
            sim: Dictionary with config for image simulator.
        """
        BaseSpectrograph.__init__(self, **kwargs)

    def _expose(self, abort_event: threading.Event) -> Tuple[fits.HDUList, Optional[str]]:
        """Actually do the exposure, should be implemented by derived classes.

        Args:
            abort_event: Event that gets triggered when exposure should be aborted.

        Returns:
            The actual image and, if present, a filename.

        Raises:
            ValueError: If exposure was not successful.
        """

        # do exposure
        log.info('Starting exposure...')
        exposure_time = 1.
        date_obs = datetime.utcnow()
        self._change_exposure_status(ExposureStatus.EXPOSING)
        self._exposing = True
        steps = 10
        for i in range(steps):
            if abort_event.is_set() or not self._exposing:
                self._exposing = False
                self._change_exposure_status(ExposureStatus.IDLE)
                raise ValueError('Exposure was aborted.')
            time.sleep(exposure_time / steps)
        self._exposing = False

        # readout
        self._change_exposure_status(ExposureStatus.READOUT)
        time.sleep(1)

        # get data
        x = np.arange(5000, 8000, 1)
        y = np.sin(x)

        # get spectrum
        hdu = fits.PrimaryHDU(y)

        # add headers
        hdu.header['DATE-OBS'] = date_obs.strftime("%Y-%m-%dT%H:%M:%S.%f")
        hdu.header['CRVAL1'] = 5000
        hdu.header['CDELT1'] = 1

        # finished
        log.info('Exposure finished.')
        self._change_exposure_status(ExposureStatus.IDLE)
        return fits.HDUList([hdu]), None

    def _abort_exposure(self) -> None:
        """Abort the running exposure. Should be implemented by derived class.

        Returns:
            Success or not.
        """
        self._exposing = False

    def get_exposure_progress(self, **kwargs: Any) -> float:
        """Returns the progress of the current exposure in percent.

        Returns:
            Progress of the current exposure in percent.
        """
        return 1.


__all__ = ['DummySpectrograph']
