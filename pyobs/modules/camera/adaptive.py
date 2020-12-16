import logging
import threading
from enum import Enum
from typing import Union
import pandas as pd
import numpy as np

from pyobs import Module
from pyobs.interfaces import ICamera, ISettings, ICameraWindow, ICameraBinning
from pyobs.modules import timeout
from pyobs.events import NewImageEvent, ExposureStatusChangedEvent
from pyobs.utils.images import Image
from pyobs.utils.photometry import SepPhotometry

log = logging.getLogger(__name__)


class AdaptiveCameraMode(Enum):
    # find brightest star within radius around centre of image
    CENTRE = 'centre',
    # find brightest star in whole image
    BRIGHTEST = 'brightest'


class AdaptiveCamera(Module, ICamera, ICameraWindow, ICameraBinning, ISettings):
    """A virtual camera for adaptive exposure times."""
    # TODO: adapt this to new ICamera interface or remove!

    def __init__(self, camera: str, mode: Union[str, AdaptiveCameraMode] = AdaptiveCameraMode.CENTRE, radius: int = 20,
                 target_counts: int = 30000, min_exptime: int = 500, max_exptime: int = 60000, history: int = 10,
                 *args, **kwargs):
        """Creates a new adaptive exposure time camera.

        Args:
            camera: Actual camera to use.
            mode: Which mode to use to find star.
            radius: Radius in px around centre for CENTRE mode.
            target_counts: Counts to aim for in target.
            min_exptime: Minimum exposure time.
            max_exptime: Maximum exposure time.
            history: Length of history.
        """
        Module.__init__(self, *args, **kwargs)

        # store
        self._camera_name = camera
        self._camera = None
        self._mode = mode if isinstance(mode, AdaptiveCameraMode) else AdaptiveCameraMode(mode)
        self._radius = radius
        self._history = []
        self._max_history = history

        # abort
        self._abort = threading.Event()

        # exposures
        self._exp_time = None
        self._exposure_count = None
        self._exposures_done = None

        # options
        self._counts = target_counts
        self._min_exp_time = min_exptime
        self._max_exp_time = max_exptime

        # SEP
        self._sep = SepPhotometry()

        # add thread
        self._process_filename = None
        self._process_lock = threading.RLock()
        self._add_thread_func(self._process_thread, True)

    def open(self):
        """Open module."""
        Module.open(self)

        # subscribe to events
        if self.comm:
            self.comm.register_event(NewImageEvent)
            self.comm.register_event(ExposureStatusChangedEvent, self._status_changed)

        # get link to camera
        self._camera = self.proxy(self._camera_name, ICamera)

    @timeout('(exposure_time+10000)*count')
    def expose(self, exposure_time: int, image_type: ICamera.ImageType, broadcast: bool = True, *args, **kwargs) -> str:
        """Starts exposure and returns reference to image.

        Args:
            exposure_time: Exposure time in seconds.
            image_type: Type of image.
            broadcast: Broadcast existence of image.

        Returns:
            Name of image that was taken.
        """

        # reset
        self._abort = threading.Event()
        self._exp_time = exposure_time
        self._exposures_done = 0

        # loop exposures
        return_filenames = []
        self._history = [exposure_time]
        count = 1
        for i in range(count):
            # abort?
            if self._abort.is_set():
                break

            # do exposure(s), never broadcast
            log.info('Starting exposure with %d/%d for %.2fs...', i+1, count, self._exp_time / 1000.)
            filenames = self._camera.expose(self._exp_time, image_type, 1, broadcast=False).wait()
            self._exposures_done += 1

            # store filename
            return_filenames.append(filenames[0])
            with self._process_lock:
                if self._process_filename is None:
                    self._process_filename = filenames[0]

            # broadcast image path
            if broadcast and self.comm:
                self.comm.send_event(NewImageEvent(filenames[0], image_type))

        # finished
        self._exposure_count = None
        self._exposures_done = None

        # return filenames
        return return_filenames

    def abort(self, *args, **kwargs):
        """Aborts the current exposure and sequence.

        Returns:
            Success or not.
        """
        self._abort.set()
        self._camera.abort().wait()

    def get_exposure_status(self, *args, **kwargs) -> ICamera.ExposureStatus:
        """Returns the current status of the camera, which is one of 'idle', 'exposing', or 'readout'.

        Returns:
            Current status of camera.
        """
        return self._camera.get_exposure_status().wait()

    def abort_sequence(self, *args, **kwargs):
        """Aborts the current sequence after current exposure.

        Raises:
            ValueError: If sequemce could not be aborted.
        """
        self._exposure_count = None
        self._exposures_done = None
        return self._camera.abort_sequence().wait()

    def get_exposures_left(self, *args, **kwargs) -> int:
        """Returns the remaining exposures.

        Returns:
            Remaining exposures
        """
        if self._exposures_done is None or self._exposure_count is None:
            return 0
        else:
            return self._exposure_count - self._exposures_done

    def get_exposure_time_left(self, *args, **kwargs) -> float:
        """Returns the remaining exposure time on the current exposure in ms.

        Returns:
            Remaining exposure time in ms.
        """
        return self._camera.get_exposures_left().wait()

    def get_exposure_progress(self, *args, **kwargs) -> float:
        """Returns the progress of the current exposure in percent.

        Returns:
            Progress of the current exposure in percent.
        """
        return self._camera.get_exposure_progress().wait()

    def _status_changed(self, event: ExposureStatusChangedEvent, sender: str, *args, **kwargs):
        """Processing status change of camera.

        Args:
            event: Status change event.
            sender: Name of sender.
        """

        # check sender
        if sender == self._camera_name:
            # resend event
            ev = ExposureStatusChangedEvent(last=event.last, current=event.current)
            self.comm.send_event(ev)

    def _process_thread(self):
        """Thread for processing images."""

        # run until closing
        while not self.closing.is_set():
            # do we have an image?
            with self._process_lock:
                filename = self._process_filename

            # got something?
            if filename is not None:
                # download image
                image = self.vfs.read_image(filename)

                # process it
                self._process_image(image)

                # reset image
                with self._process_lock:
                    self._process_filename = None

            # sleep a little
            self.closing.wait(1)

    def _process_image(self, image: Image):
        """Process image.

        Args:
            image: Image to process.
        """

        # find peak count
        peak = self._find_target(image)

        # get exposure time from image in ms
        exp_time = image.header['EXPTIME'] * 1000

        # scale exposure time
        exp_time = int(exp_time * self._counts / peak)

        # cut to limits
        exp_time = max(min(exp_time, self._max_exp_time), self._min_exp_time)

        # fill history
        self._history.append(exp_time)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

        # set it
        self._exp_time = int(np.mean(self._history))
        log.info('Setting exposure time to %.3fs.', self._exp_time / 1000.)

    def _find_target(self, image: Image) -> int:
        """Find target in image and return it's peak count.

        Args:
            image: Image to analyse.

        Returns:
            Peak count of target.
        """

        # find sources
        sources: pd.DataFrame = self._sep.find_stars(image).to_pandas()

        # which mode?
        if self._mode == AdaptiveCameraMode.BRIGHTEST:
            # sort by peak brightness and get first
            sources.sort_values('peak', ascending=False, inplace=True)
            row = sources.iloc[0]
            log.info('Found brightest star at x=%.1f, y=%.1f with peak count of %d.', row['x'], row['y'], row['peak'])
            return row['peak']

        elif self._mode == AdaptiveCameraMode.CENTRE:
            # get image centre
            cx = image.header['CRPIX1'] if 'CRPIX1' in image.header else image.header['NAXIS1'] // 2
            cy = image.header['CRPIX2'] if 'CRPIX2' in image.header else image.header['NAXIS2'] // 2

            # filter all sources within radius around centre
            r = self._radius
            filtered = sources[(sources['x'] >= cx - r) & (sources['x'] <= cx + r) &
                               (sources['y'] >= cy - r) & (sources['y'] <= cy + r)]

            # sort by peak brightness and get first
            filtered.sort_values('peak', ascending=False, inplace=True)
            row = filtered.iloc[0]
            log.info('Found brightest star at x=%.1f (dx=%.1f), y=%.1f (dy=%.1f) with peak count of %d.',
                     row['x'], row['x'] - cx, row['y'], row['y'] - cy, row['peak'])
            return row['peak']

        else:
            raise ValueError('Unknown target mode.')

    def get_settings(self, *args, **kwargs) -> dict:
        """Returns a dict of name->type pairs for settings."""
        return {
            'target_counts': 'int',
            'min_exp_time': 'int',
            'max_exp_time': 'int'
        }

    def get_setting_value(self, setting: str, *args, **kwargs):
        """Returns the value of the given setting.

        Args:
            setting: Name of setting

        Returns:
            Current value

        Raises:
            KeyError if setting does not exist
        """
        if setting == 'target_counts':
            return self._counts
        elif setting == 'min_exp_time':
            return self._min_exp_time
        elif setting == 'max_exp_time':
            return self._max_exp_time
        else:
            raise KeyError

    def set_setting_value(self, setting: str, value, *args, **kwargs):
        """Sets the value of the given setting.

        Args:
            setting: Name of setting
            value: New value

        Raises:
            KeyError if setting does not exist
        """
        if setting == 'target_counts':
            self._counts = value
        elif setting == 'min_exp_time':
            self._min_exp_time = value
        elif setting == 'max_exp_time':
            self._max_exp_time = value
        else:
            raise KeyError

    def get_full_frame(self, *args, **kwargs) -> (int, int, int, int):
        """Returns full size of CCD.

        Returns:
            Tuple with left, top, width, and height set.
        """

        # only do this, if wrapped camera doesn't support this
        if isinstance(self._camera, ICameraWindow):
            return self._camera.get_full_frame().wait()
        else:
            return 0, 0, 100, 100

    def set_window(self, left: int, top: int, width: int, height: int, *args, **kwargs):
        """Set the camera window.

        Args:
            left: X offset of window.
            top: Y offset of window.
            width: Width of window.
            height: Height of window.

        Raises:
            ValueError: If window could not be set.
        """

        # only do this, if wrapped camera doesn't support this
        if isinstance(self._camera, ICameraWindow):
            self._camera.set_window(left, top, width, height).wait()

    def get_window(self, *args, **kwargs) -> (int, int, int, int):
        """Returns the camera window.

        Returns:
            Tuple with left, top, width, and height set.
        """

        # only do this, if wrapped camera doesn't support this
        if isinstance(self._camera, ICameraWindow):
            return self._camera.get_window().wait()
        else:
            return 0, 0, 100, 100

    def set_binning(self, x: int, y: int, *args, **kwargs):
        """Set the camera binning.

        Args:
            x: X binning.
            y: Y binning.

        Raises:
            ValueError: If binning could not be set.
        """

        # only do this, if wrapped camera doesn't support this
        if isinstance(self._camera, ICameraBinning):
            self._camera.set_binning(x, y).wait()

    def get_binning(self, *args, **kwargs) -> (int, int):
        """Returns the camera binning.

        Returns:
            Tuple with x and y.
        """

        # only do this, if wrapped camera doesn't support this
        if isinstance(self._camera, ICameraBinning):
            return self._camera.get_binning().wait()
        else:
            return 1, 1


__all__ = ['AdaptiveCamera', 'AdaptiveCameraMode']
