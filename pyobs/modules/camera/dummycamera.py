import asyncio
import glob
import logging
import threading
import time
from datetime import datetime
from threading import RLock

import numpy as np
from astropy.io import fits

from pyobs.interfaces import ICamera, ICameraWindow, ICameraBinning, ICooling
from pyobs.modules.camera.basecamera import BaseCamera
from pyobs.utils.simulation.world import SimWorld

log = logging.getLogger(__name__)


class DummyCamera(BaseCamera, ICameraWindow, ICameraBinning, ICooling):
    """A dummy camera for testing."""

    def __init__(self, readout_time: float = 2, sim: dict = None, world: SimWorld = None, *args, **kwargs):
        """Creates a new dummy cammera.

        Args:
            readout_time: Readout time in seconds.
            sim: Dictionary with config for image simulator.
        """
        BaseCamera.__init__(self, *args, **kwargs)

        # add thread func
        self._add_thread_func(self._cooling_thread, True)

        # store
        self._redout_time = readout_time
        self._sim = sim if sim is not None else {}
        if 'images' not in self._sim:
            self._sim['images'] = None

        # simulated world
        self._world = world if world is not None else SimWorld()

        # init camera
        self._full_frame = (50, 0, 2048, 2064)
        self._window = self._full_frame
        self._binning = (1, 1)
        self._cooling = {'Enabled': True, 'SetPoint': -10., 'Power': 80,
                         'Temperatures':  {'CCD': 0.0, 'Backplate': 3.14}}
        self._exposing = True

        # locks
        self._coolingLock = RLock()

        # simulator
        self._sim_images = sorted(glob.glob(self._sim['images'])) if self._sim['images'] else None

    def _cooling_thread(self):
        while not self.closing.is_set():
            with self._coolingLock:
                # adjust temperature
                delta = self._cooling['Temperatures']['CCD'] - self._cooling['SetPoint']
                self._cooling['Temperatures']['CCD'] -= delta * 0.05

                # cooling power
                self._cooling['Power'] = (60. - self._cooling['Temperatures']['CCD']) / 70. * 100.

            # sleep for 1 second
            self.closing.wait(1)

    def get_full_frame(self, *args, **kwargs) -> (int, int, int, int):
        """Returns full size of CCD.

        Returns:
            Tuple with left, top, width, and height set.
        """
        return self._full_frame

    def _get_image(self, exp_time: float) -> fits.PrimaryHDU:
        """Actually get (i.e. simulate) the image."""

        # random image or pre-defined?
        if self._sim_images:
            filename = self._sim_images.pop(0)
            self._sim_images.append(filename)
            with fits.open(filename, memmap=False) as f:
                return fits.PrimaryHDU(f[0].data) #, header=f[0].header)

        else:
            left, top, width, height = self.get_window()
            data = np.random.rand(int(height / self._binning[1]), int(width / self._binning[0])) * 100.
            hdu = fits.PrimaryHDU(data.astype('uint16'))
            hdu.header['DATAMEAN'] = 1000.
            return hdu

    def _expose(self, exposure_time: int, open_shutter: bool, abort_event: threading.Event) -> fits.PrimaryHDU:
        """Actually do the exposure, should be implemented by derived classes.

        Args:
            exposure_time: The requested exposure time in ms.
            open_shutter: Whether or not to open the shutter.
            abort_event: Event that gets triggered when exposure should be aborted.

        Returns:
            The actual image.

        Raises:
            ValueError: If exposure was not successful.
        """

        # set exposure time
        log.info('Setting exposure time to {0:d}ms...'.format(exposure_time))

        # do exposure
        log.info('Starting exposure with {0:s} shutter...'.format('open' if open_shutter else 'closed'))
        date_obs = datetime.utcnow()
        self._change_exposure_status(ICamera.ExposureStatus.EXPOSING)
        self._exposing = True
        steps = 10
        for i in range(steps):
            if abort_event.is_set() or not self._exposing:
                self._exposing = False
                self._change_exposure_status(ICamera.ExposureStatus.IDLE)
                raise ValueError('Exposure was aborted.')
            time.sleep(exposure_time / 1000. / steps)
        self._exposing = False

        # readout
        self._change_exposure_status(ICamera.ExposureStatus.READOUT)
        time.sleep(self._redout_time)

        # get image
        hdu = self._get_image(exposure_time)

        # add headers
        hdu.header['EXPTIME'] = exposure_time / 1000.
        hdu.header['DATE-OBS'] = date_obs.strftime("%Y-%m-%dT%H:%M:%S.%f")
        hdu.header['XBINNING'] = hdu.header['DET-BIN1'] = (self._binning[0], 'Binning factor used on X axis')
        hdu.header['YBINNING'] = hdu.header['DET-BIN2'] = (self._binning[1], 'Binning factor used on Y axis')
        hdu.header['XORGSUBF'] = (self._window[0], 'Subframe origin on X axis')
        hdu.header['YORGSUBF'] = (self._window[1], 'Subframe origin on Y axis')

        # biassec/trimsec
        self.set_biassec_trimsec(hdu.header, *self._full_frame)

        # finished
        log.info('Exposure finished.')
        self._change_exposure_status(ICamera.ExposureStatus.IDLE)
        return hdu

    def _abort_exposure(self):
        """Abort the running exposure. Should be implemented by derived class.

        Returns:
            Success or not.
        """
        self._exposing = False

    def get_window(self, *args, **kwargs) -> (int, int, int, int):
        """Returns the camera window.

        Returns:
            Tuple with left, top, width, and height set.
        """
        return self._window

    def set_window(self, left: float, top: float, width: float, height: float, *args, **kwargs):
        """Set the camera window.

        Args:
            left: X offset of window.
            top: Y offset of window.
            width: Width of window.
            height: Height of window.

        Raises:
            ValueError: If binning could not be set.
        """
        log.info("Set window to %dx%d at %d,%d.", width, height, top, left)
        self._window = (left, top, width, height)

    def get_binning(self, *args, **kwargs) -> (int, int):
        """Returns the camera binning.

        Returns:
            Tuple with x and y.
        """
        return self._binning

    def set_binning(self, x: int, y: int, *args, **kwargs):
        """Set the camera binning.

        Args:
            x: X binning.
            y: Y binning.

        Raises:
            ValueError: If binning could not be set.
        """
        log.info("Set binning to %dx%d.", x, y)
        self._binning = (x, y)

    def set_cooling(self, enabled: bool, setpoint: float, *args, **kwargs):
        """Enables/disables cooling and sets setpoint.

        Args:
            enabled: Enable or disable cooling.
            setpoint: Setpoint in celsius for the cooling.

        Raises:
            ValueError: If cooling could not be set.
        """

        # log
        if enabled:
            log.info('Enabling cooling with a setpoint of %.2f°C.', setpoint)
        else:
            log.info('Disabling cooling.')

        # set
        with self._coolingLock:
            self._cooling = {
                'Enabled': enabled,
                'SetPoint': setpoint,
                'Power': self._cooling['Power'],
                'Temperatures': self._cooling['Temperatures']
            }

    def get_cooling_status(self, *args, **kwargs) -> (bool,  float, float, dict):
        """Returns the current status for the cooling.

        Returns:
            Tuple containing:
                Enabled (bool):         Whether the cooling is enabled
                SetPoint (float):       Setpoint for the cooling in celsius.
                Power (float):          Current cooling power in percent or None.
                Temperatures (dict):    Dictionary of sensor name/value pairs with temperatures
        """
        c = self._cooling
        return c['Enabled'], c['SetPoint'], c['Power']

    def get_temperatures(self, *args, **kwargs) -> dict:
        """Returns all temperatures measured by this module.

        Returns:
            Dict containing temperatures.
        """
        return self._cooling['Temperatures']


__all__ = ['DummyCamera']
