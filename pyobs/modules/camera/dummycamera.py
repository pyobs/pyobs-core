import glob
import logging
import threading
import time
from datetime import datetime
from threading import RLock
from typing import Tuple, NamedTuple, Dict

from astropy.io import fits

from pyobs.interfaces import ICamera, ICameraWindow, ICameraBinning, ICooling
from pyobs.modules.camera.basecamera import BaseCamera
from pyobs.images import Image
from pyobs.utils.enums import ExposureStatus

log = logging.getLogger(__name__)


class CoolingStatus(NamedTuple):
    enabled: bool = True
    set_point: float = -10.
    power: float = 80.
    temperatures: Dict[str, float] = {'CCD': 0., 'Back': 3.14}


class DummyCamera(BaseCamera, ICameraWindow, ICameraBinning, ICooling):
    """A dummy camera for testing."""

    def __init__(self, readout_time: float = 2, sim: dict = None, world: 'SimWorld' = None, *args, **kwargs):
        """Creates a new dummy cammera.

        Args:
            readout_time: Readout time in seconds.
            sim: Dictionary with config for image simulator.
        """
        BaseCamera.__init__(self, *args, **kwargs)

        # add thread func
        self.add_thread_func(self._cooling_thread, True)

        # store
        self._readout_time = readout_time
        self._sim = sim if sim is not None else {}
        if 'images' not in self._sim:
            self._sim['images'] = None

        # simulated world
        from pyobs.utils.simulation.world import SimCamera
        self._world = world if world is not None else \
            self.add_child_object({'class': 'pyobs.utils.simulation.world.SimWorld'})
        self._camera: SimCamera = self._world.camera

        # init camera
        self._cooling = CoolingStatus()
        self._exposing = True

        # locks
        self._coolingLock = RLock()

        # simulator
        self._sim_images = sorted(glob.glob(self._sim['images'])) if self._sim['images'] else None

    def _cooling_thread(self):
        while not self.closing.is_set():
            with self._coolingLock:
                # adjust temperature
                temps = self._cooling.temperatures
                temps['CCD'] -= (self._cooling.temperatures['CCD'] - self._cooling.set_point) * 0.05

                # cooling power
                power = (60. - self._cooling.temperatures['CCD']) / 70. * 100.

                # create new object
                self._cooling = CoolingStatus(enabled=self._cooling.enabled, set_point=self._cooling.set_point,
                                              power=power, temperatures=temps)

            # sleep for 1 second
            self.closing.wait(1)

    def get_full_frame(self, *args, **kwargs) -> Tuple[int, int, int, int]:
        """Returns full size of CCD.

        Returns:
            Tuple with left, top, width, and height set.
        """
        return self._camera.full_frame

    def _get_image(self, exp_time: float, open_shutter: bool) -> Image:
        """Actually get (i.e. simulate) the image."""

        # random image or pre-defined?
        if self._sim_images:
            filename = self._sim_images.pop(0)
            self._sim_images.append(filename)
            return Image.from_file(filename)

        else:
            image = self._camera.get_image(exp_time, open_shutter)
            return image

    def _expose(self, exposure_time: float, open_shutter: bool, abort_event: threading.Event) -> fits.PrimaryHDU:
        """Actually do the exposure, should be implemented by derived classes.

        Args:
            exposure_time: The requested exposure time in seconds.
            open_shutter: Whether or not to open the shutter.
            abort_event: Event that gets triggered when exposure should be aborted.

        Returns:
            The actual image.

        Raises:
            ValueError: If exposure was not successful.
        """

        # do exposure
        log.info('Starting exposure with {0:s} shutter...'.format('open' if open_shutter else 'closed'))
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
        time.sleep(self._readout_time)

        # get image
        hdu = self._get_image(exposure_time, open_shutter)

        # add headers
        hdu.header['EXPTIME'] = exposure_time
        hdu.header['DATE-OBS'] = date_obs.strftime("%Y-%m-%dT%H:%M:%S.%f")
        hdu.header['XBINNING'] = hdu.header['DET-BIN1'] = (self._camera.binning[0], 'Binning factor used on X axis')
        hdu.header['YBINNING'] = hdu.header['DET-BIN2'] = (self._camera.binning[1], 'Binning factor used on Y axis')
        hdu.header['XORGSUBF'] = (self._camera.window[0], 'Subframe origin on X axis')
        hdu.header['YORGSUBF'] = (self._camera.window[1], 'Subframe origin on Y axis')

        # biassec/trimsec
        self.set_biassec_trimsec(hdu.header, *self._camera.full_frame)

        # finished
        log.info('Exposure finished.')
        self._change_exposure_status(ExposureStatus.IDLE)
        return hdu

    def _abort_exposure(self):
        """Abort the running exposure. Should be implemented by derived class.

        Returns:
            Success or not.
        """
        self._exposing = False

    def get_window(self, *args, **kwargs) -> Tuple[int, int, int, int]:
        """Returns the camera window.

        Returns:
            Tuple with left, top, width, and height set.
        """
        return self._camera.window

    def set_window(self, left: int, top: int, width: int, height: int, *args, **kwargs):
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
        self._camera.window = (left, top, width, height)

    def get_binning(self, *args, **kwargs) -> Tuple[int, int]:
        """Returns the camera binning.

        Returns:
            Tuple with x and y.
        """
        return self._camera.binning

    def set_binning(self, x: int, y: int, *args, **kwargs):
        """Set the camera binning.

        Args:
            x: X binning.
            y: Y binning.

        Raises:
            ValueError: If binning could not be set.
        """
        log.info("Set binning to %dx%d.", x, y)
        self._camera.binning = (x, y)

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
            self._cooling = CoolingStatus(enabled=enabled, set_point=setpoint, power=self._cooling.power,
                                          temperatures=self._cooling.temperatures)

    def get_cooling_status(self, *args, **kwargs) -> Tuple[bool, float, float]:
        """Returns the current status for the cooling.

        Returns:
            Tuple containing:
                Enabled (bool):         Whether the cooling is enabled
                SetPoint (float):       Setpoint for the cooling in celsius.
                Power (float):          Current cooling power in percent or None.
                Temperatures (dict):    Dictionary of sensor name/value pairs with temperatures
        """
        with self._coolingLock:
            return self._cooling.enabled, self._cooling.set_point, self._cooling.power

    def get_temperatures(self, *args, **kwargs) -> dict:
        """Returns all temperatures measured by this module.

        Returns:
            Dict containing temperatures.
        """
        return self._cooling.temperatures

    def _set_config_readout_time(self, readout_time):
        """Set readout time."""
        self._readout_time = readout_time

    def _get_config_readout_time(self):
        """Returns readout time."""
        return self._readout_time


__all__ = ['DummyCamera']
