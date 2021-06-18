import datetime
import logging
import math
import os
import threading
import warnings
from typing import Tuple, Optional, Dict, Any, NamedTuple
import numpy as np
from astropy.io import fits
import astropy.units as u

from pyobs.comm import TimeoutException, InvocationException
from pyobs.utils.enums import ImageType, ExposureStatus
from pyobs.images import Image

from pyobs.utils.time import Time
from pyobs.utils.fits import format_filename

from pyobs.modules import Module
from pyobs.events import NewImageEvent, ExposureStatusChangedEvent
from pyobs.interfaces import ICamera, IFitsHeaderProvider, IAbortable, ICameraExposureTime, IImageType
from pyobs.modules import timeout
from .basecam import BaseCam

log = logging.getLogger(__name__)


class CameraException(Exception):
    pass


class ExposureInfo(NamedTuple):
    """Info about a running exposure."""
    start: datetime.datetime
    exposure_time: float


def calc_expose_timeout(camera, *args, **kwargs):
    """Calculates timeout for expose()."""
    return camera.get_exposure_time() + 30


class BaseCamera(BaseCam, ICamera, ICameraExposureTime, IImageType, IAbortable):
    """Base class for all camera modules."""
    __module__ = 'pyobs.modules.camera'

    def __init__(self, fits_namespaces: list = None, *args, **kwargs):
        """Creates a new BaseCamera.

        Args:
            fits_namespaces: List of namespaces for FITS headers that this camera should request
        """
        BaseCam.__init__(self, *args, **kwargs)

        # store
        self._fits_namespaces = fits_namespaces
        self._image_type = ImageType.OBJECT

        # init camera
        self._exposure: Optional[ExposureInfo] = None
        self._camera_status = ExposureStatus.IDLE

        # multi-threading
        self._expose_lock = threading.Lock()
        self.expose_abort = threading.Event()

    def open(self):
        """Open module."""
        BaseCam.open(self)

        # subscribe to events
        if self.comm:
            self.comm.register_event(NewImageEvent)
            self.comm.register_event(ExposureStatusChangedEvent)

    def set_image_type(self, image_type: ImageType, *args, **kwargs):
        """Set the image type.

        Args:
            image_type: New image type.
        """
        log.info('Setting image type to %s...', image_type)
        self._image_type = image_type

    def get_image_type(self, *args, **kwargs) -> ImageType:
        """Returns the current image type.

        Returns:
            Current image type.
        """
        return self._image_type

    def _change_exposure_status(self, status: ExposureStatus):
        """Change exposure status and send event,

        Args:
            status: New exposure status.
        """

        # send event, if it changed
        if self._camera_status != status:
            self.comm.send_event(ExposureStatusChangedEvent(self._camera_status, status))

        # set it
        self._camera_status = status

    def get_exposure_status(self, *args, **kwargs) -> ExposureStatus:
        """Returns the current status of the camera, which is one of 'idle', 'exposing', or 'readout'.

        Returns:
            Current status of camera.
        """
        return self._camera_status

    def get_exposure_time_left(self, *args, **kwargs) -> float:
        """Returns the remaining exposure time on the current exposure in seconds.

        Returns:
            Remaining exposure time in seconds.
        """

        # if we're not exposing, there is nothing left
        if self._exposure is None:
            return 0.

        # calculate difference between start of exposure and now, and return in ms
        duration = datetime.timedelta(seconds=self._exposure.exposure_time)
        diff = self._exposure.start + duration - datetime.datetime.utcnow()
        return diff.total_seconds()

    def get_exposure_progress(self, *args, **kwargs) -> float:
        """Returns the progress of the current exposure in percent.

        Returns:
            Progress of the current exposure in percent.
        """

        # if we're not exposing, there is no progress
        if self._exposure is None:
            return 0.

        # calculate difference between start of exposure and now
        diff = datetime.datetime.utcnow() - self._exposure[0]

        # zero exposure time?
        if self._exposure.exposure_time == 0. or self._camera_status == ExposureStatus.READOUT:
            return 100.
        else:
            # return max of 100
            percentage = diff.total_seconds() / self._exposure[1] * 100.
            return min(percentage, 100.)

    def _expose(self, exposure_time: float, open_shutter: bool, abort_event: threading.Event) -> Image:
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
        raise NotImplementedError

    def __expose(self, exposure_time: float, image_type: ImageType, broadcast: bool) \
            -> Tuple[Optional[Image], Optional[str]]:
        """Wrapper for a single exposure.

        Args:
            exposure_time: The requested exposure time in seconds.
            open_shutter: Whether or not to open the shutter.
            broadcast: Whether or not the new image should be broadcasted.

        Returns:
            Tuple of the image itself and its filename.

        Raises:
            ValueError: If exposure was not successful.
        """
        fits_header_futures = {}
        if self.comm:
            # get clients that provide fits headers
            clients = self.comm.clients_with_interface(IFitsHeaderProvider)

            # create and run a threads in which the fits headers are fetched
            for client in clients:
                log.info('Requesting FITS headers from %s...', client)
                future = self.comm.execute(client, 'get_fits_headers', self._fits_namespaces)
                fits_header_futures[client] = future

        # open the shutter?
        open_shutter = image_type not in [ImageType.BIAS, ImageType.DARK]

        # do the exposure
        self._exposure = ExposureInfo(start=datetime.datetime.utcnow(), exposure_time=exposure_time)
        try:
            image = self._expose(exposure_time, open_shutter, abort_event=self.expose_abort)
            if image is None:
                self._exposure = None
                return None, None
        except:
            # exposure was not successful (aborted?), so reset everything
            self._exposure = None
            raise

        # flip it?
        if self._flip:
            # do we have three dimensions in array? need this for deciding which axis to flip
            is_3d = len(image.data.shape) == 3

            # flip image and make contiguous again
            image.data = np.ascontiguousarray(np.flip(image.data, axis=1 if is_3d else 0))

        # add HDU name
        image.header['EXTNAME'] = 'SCI'

        # add image type
        image.header['IMAGETYP'] = image_type.value

        # get fits headers from other clients
        for client, future in fits_header_futures.items():
            # join thread
            log.info('Fetching FITS headers from %s...', client)
            try:
                headers = future.wait()
            except TimeoutException:
                log.warning('Fetching FITS headers from %s timed out.', client)
                continue
            except InvocationException as e:
                log.warning('Could not fetch FITS headers from %s: %s.', client, e.get_message())
                continue

            # add them to fits file
            if headers:
                log.info('Adding additional FITS headers from %s...' % client)
                for key, value in headers.items():
                    # if value is not a string, it may be a list of value and comment
                    if type(value) is list:
                        # convert list to tuple
                        image.header[key] = tuple(value)
                    else:
                        image.header[key] = value

        # add static fits headers
        for key, value in self._fits_headers.items():
            image.header[key] = tuple(value)

        # add more fits headers
        log.info("Adding FITS headers...")
        self._add_fits_headers(image.header)

        # don't want to save?
        if self._filenames is None:
            return image, None

        # create a temporary filename
        filename = format_filename(image.header, self._filenames)
        image.header['ORIGNAME'] = (os.path.basename(filename), 'The original file name')
        image.header['FNAME'] = (os.path.basename(filename), 'FITS file file name')
        if filename is None:
            raise ValueError('Cannot save image.')

        # upload file
        try:
            log.info('Uploading image to file server...')
            self.vfs.write_image(filename, image)
        except FileNotFoundError:
            raise ValueError('Could not upload image.')

        # broadcast image path
        if broadcast and self.comm:
            log.info('Broadcasting image ID...')
            self.comm.send_event(NewImageEvent(filename, image_type))

        # return image and unique
        self._exposure = None
        log.info('Finished image %s.', filename)
        return image, filename

    @timeout(calc_expose_timeout)
    def expose(self, broadcast: bool = True, *args, **kwargs) -> str:
        """Starts exposure and returns reference to image.

        Args:
            exposure_time: Exposure time in seconds.
            broadcast: Broadcast existence of image.

        Returns:
            Name of image that was taken.
        """

        # acquire lock
        log.info('Acquiring exclusive lock on camera...')
        if not self._expose_lock.acquire(blocking=False):
            raise ValueError('Could not acquire camera lock for expose().')

        # make sure that we release the lock
        try:
            # are we exposing?
            if self._camera_status != ExposureStatus.IDLE:
                raise CameraException('Cannot start new exposure because camera is not idle.')

            # expose
            image, filename = self.__expose(self._exposure_time, self._image_type, broadcast)
            if image is None:
                raise ValueError('Could not take image.')
            else:
                if filename is None:
                    raise ValueError('Image has not been saved, so cannot be retrieved by filename.')

            # return filename
            return filename

        finally:
            # release lock
            log.info('Releasing exclusive lock on camera...')
            self._expose_lock.release()

    def _abort_exposure(self):
        """Abort the running exposure. Should be implemented by derived class.

        Raises:
            ValueError: If an error occured.
        """
        pass

    def abort(self, *args, **kwargs):
        """Aborts the current exposure and sequence.

        Returns:
            Success or not.
        """

        # set abort event
        log.info('Aborting current image and sequence...')
        self._exposures_left = 0
        self.expose_abort.set()

        # do camera-specific abort
        self._abort_exposure()

        # wait for lock and unset event
        acquired = self._expose_lock.acquire(blocking=True, timeout=5.)
        self.expose_abort.clear()
        if acquired:
            self._expose_lock.release()
        else:
            raise ValueError('Could not abort exposure.')

    def list_binnings(self, *args, **kwargs) -> list:
        """List available binnings.

        Returns:
            List of available binnings as (x, y) tuples.
        """

        warnings.warn('The default implementation for list_binnings() in BaseCamera will be removed in future versions',
                      DeprecationWarning)
        return [(1, 1), (2, 2), (3, 3)]


__all__ = ['BaseCamera', 'CameraException']
