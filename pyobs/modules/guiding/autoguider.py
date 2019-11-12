import logging
import threading
from typing import Union
import astropy.units as u
import numpy as np
from astropy.coordinates import SkyCoord, AltAz
from astropy.io import fits
from astropy.time import Time
from scipy.interpolate import UnivariateSpline
from scipy.optimize import fmin
from astropy.wcs import WCS
import re

from pyobs import PyObsModule
from pyobs.events import NewImageEvent
from pyobs.interfaces import ITelescope, IAutoGuiding, IStoppable, IEquitorialMount, IAltAzMount, ICamera
from pyobs.object import get_object
from pyobs.utils.guiding.base import BaseGuider
from pyobs.utils.pid import PID


log = logging.getLogger(__name__)


class AutoGuider(PyObsModule, IAutoGuiding):
    """An auto-guiding system."""

    def __init__(self, camera: Union[str, ICamera], telescope: Union[str, ITelescope], exp_time: float = None,
                 guider: Union[dict, BaseGuider] = None, *args, **kwargs):
        """Initializes a new auto guiding system.

        Args:
            camera: Camera to use.
            telescope: Telescope to use.
            exp_time: Exposure time
            guider: Auto-guider to use
        """
        PyObsModule.__init__(self, *args, **kwargs)

        # store
        self._camera = camera
        self._telescope = telescope
        self._exp_time = exp_time
        self._enabled = False

        # add thread func
        self._add_thread_func(self._auto_guiding, True)

        # create auto-guiding system
        self._guider = get_object(guider, BaseGuider)

    def open(self):
        """Open module."""
        PyObsModule.open(self)

        # check camera
        try:
            self.proxy(self._camera, ICamera)
        except ValueError:
            log.warning('Given camera does not exist or is not of correct type at the moment.')

        # check telescope
        try:
            self.proxy(self._telescope, ITelescope)
        except ValueError:
            log.warning('Given telescope does not exist or is not of correct type at the moment.')

    def start(self, *args, **kwargs) -> bool:
        """Starts/resets auto-guiding."""
        self._enabled = True

    def stop(self, *args, **kwargs):
        """Stops auto-guiding."""
        self._enabled = False

    def is_running(self, *args, **kwargs) -> bool:
        """Whether auto-guiding is running.

        Returns:
            Auto-guiding is running.
        """
        return self._enabled

    def _auto_guiding(self):
        # run until closed
        while not self.closing.is_set():
            # not running?
            if not self._enabled:
                self.closing.sleep(1)
                continue

            # get telescope and camera
            telescope: ITelescope = self.proxy(self._telescope, ITelescope)
            camera: ICamera = self.proxy(self._camera, ICamera)

            # take image
            image = camera.expose(self._exp_time, ICamera.ImageType.OBJECT, 1, False)

            # process it
            self._guider(image, telescope)

    def add_image(self, event: NewImageEvent, sender: str, *args, **kwargs):
        """Processes an image asynchronously, returns immediately.

        Args:
            filename: Filename of image to process.
        """

        log.info('Received new image from %s.', sender)

        # if not enabled, just ignore
        if not self._enabled:
            return

        # download image
        try:
            with self.open_file(event.filename, 'rb') as f:
                tmp = fits.open(f, memmap=False)
                data = fits.PrimaryHDU(data=tmp[0].data, header=tmp[0].header)
                tmp.close()
        except FileNotFoundError:
            log.error('Could not download image.')
            return

        # we only accept OBJECT images
        if data.header['IMAGETYP'] != 'object':
            return

        # store filename as next image to process
        with self._lock:
            # do we have a filename in here already?
            if self._next_image:
                log.warning('Last image still being processed by auto-guiding, skipping new one.')
                return

            # store it
            self._next_image = data


__all__ = ['AutoGuidingProjection']
