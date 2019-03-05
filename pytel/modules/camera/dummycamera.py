import asyncio
import glob
import logging
import threading
import time
from datetime import datetime
from threading import RLock

import numpy as np
from astropy.io import fits

from pytel.interfaces import ICamera, ICameraWindow, ICameraBinning, ICooling
from pytel.modules.camera.basecamera import BaseCamera


log = logging.getLogger(__name__)


class DummyCamera(BaseCamera, ICamera, ICameraWindow, ICameraBinning, ICooling):
    """A dummy camera for testing."""

    def __init__(self, readout_time: float = 2, sim: dict = None, *args, **kwargs):
        """Creates a new dummy cammera.

        Args:
            readout_time: Readout time in seconds.
            sim: Dictionary with config for image simulator.
        """
        BaseCamera.__init__(self, thread_funcs=self._cooling_thread, *args, **kwargs)

        # store
        self._redout_time = readout_time
        self._sim = sim if sim is not None else {}
        if 'images' not in self._sim:
            self._sim['images'] = None

        # init camera
        self._window = {'left': 50, 'top': 0, 'width': 2048, 'height': 2064}
        self._binning = {'x': 1, 'y': 1}
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

    def get_full_frame(self, *args, **kwargs) -> dict:
        """Returns full size of CCD.

        Returns:
            Dictionary with left, top, width, and height set.
        """
        return {'left': 50, 'top': 0, 'width': 2048, 'height': 2064}

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
        self._camera_status = ICamera.CameraStatus.EXPOSING
        self._exposing = True
        steps = 10
        for i in range(steps):
            if abort_event.is_set() or not self._exposing:
                self._exposing = False
                self._camera_status = ICamera.CameraStatus.IDLE
                raise ValueError('Exposure was aborted.')
            time.sleep(exposure_time / 1000. / steps)
        self._exposing = False

        # readout
        self._camera_status = ICamera.CameraStatus.READOUT
        time.sleep(self._redout_time)

        # random image or pre-defined?
        if self._sim_images:
            filename = self._sim_images.pop(0)
            self._sim_images.append(filename)
            with fits.open(filename, memmap=False) as f:
                hdu = fits.PrimaryHDU(data=f[0].data, header=f[0].header)

        else:
            wnd = self.get_window()
            data = np.random.rand(int(wnd['height'] / self._binning['y']),
                                  int(wnd['width'] / self._binning['x'])) * 100.
            hdu = fits.PrimaryHDU(data.astype('uint16'))
            hdu.header['EXPTIME'] = exposure_time / 1000.

        # add headers
        hdu.header['DATE-OBS'] = date_obs.strftime("%Y-%m-%dT%H:%M:%S.%f")
        hdu.header['XBINNING'] = hdu.header['DET-BIN1'] = (self._binning['x'], 'Binning factor used on X axis')
        hdu.header['YBINNING'] = hdu.header['DET-BIN2'] = (self._binning['y'], 'Binning factor used on Y axis')
        hdu.header['XORGSUBF'] = (self._window['left'], 'Subframe origin on X axis')
        hdu.header['YORGSUBF'] = (self._window['top'], 'Subframe origin on Y axis')

        # biassec/trimsec
        self.set_biassec_trimsec(hdu.header, 50, 0, 2048, 2064)

        # finished
        log.info('Exposure finished.')
        self._camera_status = ICamera.CameraStatus.IDLE
        return hdu

    def _abort_exposure(self):
        """Abort the running exposure. Should be implemented by derived class.

        Returns:
            Success or not.
        """
        self._exposing = False

    def get_window(self, *args, **kwargs) -> dict:
        """Returns the camera window.

        Returns:
            Dictionary with left, top, width, and height set.
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
        self._window = {'left': left, 'top': top, 'width': width, 'height': height}

    def get_binning(self, *args, **kwargs) -> dict:
        """Returns the camera binning.

        Returns:
            Dictionary with x and y.
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
        self._binning = {'x': x, 'y': y}

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

    def status(self, *args, **kwargs) -> dict:
        """Returns status of camera.

        Returns:
            Current status as dictionary.
        """
        
        # get status from parent
        status = super().status()

        # add more
        with self._coolingLock:
            status['ICooling'] = dict(self._cooling)
        return status


__all__ = ['DummyCamera']
