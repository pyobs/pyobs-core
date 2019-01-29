import asyncio
import glob
import logging
import threading
import time
from datetime import datetime
from threading import RLock, Thread

import numpy as np
from astropy.io import fits

from pytel.interfaces import ICamera, ICameraWindow, ICameraBinning, ICooling
from pytel.modules.camera.basecamera import BaseCamera


log = logging.getLogger(__name__)


class DummyCamera(BaseCamera, ICamera, ICameraWindow, ICameraBinning, ICooling):
    def __init__(self, sim: dict = None, *args, **kwargs):
        """Creates a new dummy cammera.

        Args:
            sim: Dictionary with config for image simulator.
        """
        BaseCamera.__init__(self, thread_funcs=self._status, *args, **kwargs)

        # store
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
        self._statusLock = RLock()

        # simulator
        self._sim_images = sorted(glob.glob(self._sim['images'])) if self._sim['images'] else None

        # create thread function
        self._status = {}
        self._lock = RLock()

    def _status(self):
        while not self.closing.is_set():
            with self._statusLock:
                # config
                c = self._cooling

            # adjust temperature
            delta = c['Temperatures']['CCD'] - c['SetPoint']
            c['Temperatures']['CCD'] -= delta * 0.05

            # cooling power
            c['Power'] = (60. - c['Temperatures']['CCD']) / 70. * 100.

            # sleep for 1 second
            self.closing.wait(1.0)

    def get_full_frame(self, *args, **kwargs) -> dict:
        return {'left': 50, 'top': 0, 'width': 2048, 'height': 2064}

    def _expose(self, exposure_time: int, open_shutter: bool, abort_event: threading.Event) -> fits.ImageHDU:
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
                return None
            time.sleep(exposure_time / 1000. / steps)
        self._exposing = False

        # readout
        self._camera_status = ICamera.CameraStatus.READOUT
        time.sleep(2.)

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

    def _abort_exposure(self) -> bool:
        """Aborts the current exposure.

        Returns:
            bool: True if successful, otherwise False.
        """
        self._exposing = False
        return True

    def get_window(self, *args, **kwargs) -> dict:
        return self._window

    def set_window(self, left: int, top: int, width: int, height: int, *args, **kwargs) -> bool:
        log.info("Set window to %dx%d at %d,%d.", width, height, top, left)
        self._window = {'left': left, 'top': top, 'width': width, 'height': height}
        return True

    def get_binning(self, *args, **kwargs):
        return self._binning

    def set_binning(self, x: int, y: int, *args, **kwargs):
        log.info("Set binning to %dx%d.", x, y)
        self._binning = {'x': x, 'y': y}
        return True

    def set_cooling(self, enabled: bool, setpoint: float, *args, **kwargs) -> bool:
        # log
        if enabled:
            log.info('Enabling cooling with a setpoint of %.2f°C.', setpoint)
        else:
            log.info('Disabling cooling.')

        # set
        with self._statusLock:
            self._cooling = {
                'Enabled': enabled,
                'SetPoint': setpoint,
                'Power': self._cooling['Power'],
                'Temperatures': self._cooling['Temperatures']
            }
        return True

    def status(self, *args, **kwargs) -> dict:
        # get status from parent
        status = super().status()

        # add more
        with self._statusLock:
            status['ICooling'] = dict(self._cooling)
        return status


__all__ = ['DummyCamera']
