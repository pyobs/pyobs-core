import datetime
import logging
import threading
import warnings
from typing import Tuple, Optional, Dict, Any, NamedTuple
import numpy as np
from astropy.io import fits

from pyobs.mixins.imagegrabber import ImageGrabberMixin
from pyobs.utils.enums import ImageType, ExposureStatus
from pyobs.images import Image
from pyobs.modules import Module
from pyobs.events import NewImageEvent, ExposureStatusChangedEvent
from pyobs.interfaces import ICamera, IExposureTime, IImageType
from pyobs.modules import timeout

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


class BaseCamera(Module, ImageGrabberMixin, ICamera, IExposureTime, IImageType):
    """Base class for all camera modules."""
    __module__ = 'pyobs.modules.camera'

    def __init__(self, fits_headers: Optional[Dict[str, Any]] = None, centre: Optional[Tuple[float, float]] = None,
                 rotation: float = 0., flip: bool = False,
                 filenames: str = '/cache/pyobs-{DAY-OBS|date:}-{FRAMENUM|string:04d}-{IMAGETYP|type}00.fits.gz',
                 fits_namespaces: list = None, *args, **kwargs):
        """Creates a new BaseCamera.

        Args:
            fits_headers: Additional FITS headers.
            centre: (x, y) tuple of camera centre.
            rotation: Rotation east of north.
            flip: Whether or not to flip the image along its first axis.
            filenames: Template for file naming.
            fits_namespaces: List of namespaces for FITS headers that this camera should request
        """
        Module.__init__(self, *args, **kwargs)
        ImageGrabberMixin.__init__(self, fits_namespaces=fits_namespaces, fits_headers=fits_headers, centre=centre,
                                   rotation=rotation, filenames=filenames)

        # check
        if self.comm is None:
            log.warning('No comm module given, will not be able to signal new images!')

        # store
        self._flip = flip
        self._exposure_time: float = 0.
        self._image_type = ImageType.OBJECT

        # init camera
        self._exposure: Optional[ExposureInfo] = None
        self._camera_status = ExposureStatus.IDLE

        # multi-threading
        self._expose_lock = threading.Lock()
        self.expose_abort = threading.Event()

    def open(self):
        """Open module."""
        Module.open(self)

        # subscribe to events
        if self.comm:
            self.comm.register_event(NewImageEvent)
            self.comm.register_event(ExposureStatusChangedEvent)

    def set_exposure_time(self, exposure_time: float, *args, **kwargs):
        """Set the exposure time in seconds.

        Args:
            exposure_time: Exposure time in seconds.

        Raises:
            ValueError: If exposure time could not be set.
        """
        log.info('Setting exposure time to %.5fs...', exposure_time)
        self._exposure_time = exposure_time

    def get_exposure_time(self, *args, **kwargs) -> float:
        """Returns the exposure time in seconds.

        Returns:
            Exposure time in seconds.
        """
        return self._exposure_time

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

        # request fits headers
        header_futures = self.request_fits_headers()

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

        # add fits headers and format filename
        self.add_requested_fits_headers(image, header_futures)
        self.add_fits_headers(image)
        filename = self.format_filename(image)

        # don't want to save?
        if filename is None:
            return image, None

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
        warnings.warn('expose() has been replaced by grab_image() and will be removed in a future version.',
                      DeprecationWarning)
        return self.grab_image(broadcast, *args, **kwargs)

    @timeout(calc_expose_timeout)
    def grab_image(self, broadcast: bool = True, *args, **kwargs) -> str:
        """Grabs an image ans returns reference.

        Args:
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

    @staticmethod
    def set_biassec_trimsec(hdr: fits.Header, left: int, top: int, width: int, height: int):
        """Calculates and sets the BIASSEC and TRIMSEC areas.

        Args:
            hdr:    FITS header (in/out)
            left:   left edge of data area
            top:    top edge of data area
            width:  width of data area
            height: height of data area
        """

        # get image area in unbinned coordinates
        img_left = hdr['XORGSUBF']
        img_top = hdr['YORGSUBF']
        img_width = hdr['NAXIS1'] * hdr['XBINNING']
        img_height = hdr['NAXIS2'] * hdr['YBINNING']

        # get intersection
        is_left = max(left, img_left)
        is_right = min(left+width, img_left+img_width)
        is_top = max(top, img_top)
        is_bottom = min(top+height, img_top+img_height)

        # for simplicity we allow prescan/overscan only in one dimension
        if (left < is_left or left+width > is_right) and (top < is_top or top+height > is_bottom):
            log.warning('BIASSEC/TRIMSEC can only be calculated with a prescan/overscan on one axis only.')
            return False

        # comments
        c1 = 'Bias overscan area [x1:x2,y1:y2] (binned)'
        c2 = 'Image area [x1:x2,y1:y2] (binned)'

        # rectangle empty?
        if is_right <= is_left or is_bottom <= is_top:
            # easy case, all is BIASSEC, no TRIMSEC at all
            hdr['BIASSEC'] = ('[1:%d,1:%d]' % (hdr['NAXIS1'], hdr['NAXIS2']), c1)
            return

        # we got a TRIMSEC, calculate its binned and windowd coordinates
        is_left_binned = np.floor((is_left - hdr['XORGSUBF']) / hdr['XBINNING']) + 1
        is_right_binned = np.ceil((is_right - hdr['XORGSUBF']) / hdr['XBINNING'])
        is_top_binned = np.floor((is_top - hdr['YORGSUBF']) / hdr['YBINNING']) + 1
        is_bottom_binned = np.ceil((is_bottom - hdr['YORGSUBF']) / hdr['YBINNING'])

        # set it
        hdr['TRIMSEC'] = ('[%d:%d,%d:%d]' % (is_left_binned, is_right_binned, is_top_binned, is_bottom_binned), c2)
        hdr['DATASEC'] = ('[%d:%d,%d:%d]' % (is_left_binned, is_right_binned, is_top_binned, is_bottom_binned), c2)

        # now get BIASSEC -- whatever we do, we only take the last (!) one
        # which axis?
        if img_left+img_width > left+width:
            left_binned = np.floor((is_right - hdr['XORGSUBF']) / hdr['XBINNING']) + 1
            hdr['BIASSEC'] = ('[%d:%d,1:%d]' % (left_binned, hdr['NAXIS1'], hdr['NAXIS2']), c1)
        elif img_left < left:
            right_binned = np.ceil((is_left - hdr['XORGSUBF']) / hdr['XBINNING'])
            hdr['BIASSEC'] = ('[1:%d,1:%d]' % (right_binned, hdr['NAXIS2']), c1)
        elif img_top+img_height > top+height:
            top_binned = np.floor((is_bottom - hdr['YORGSUBF']) / hdr['YBINNING']) + 1
            hdr['BIASSEC'] = ('[1:%d,%d:%d]' % (hdr['NAXIS1'], top_binned, hdr['NAXIS2']), c1)
        elif img_top < top:
            bottom_binned = np.ceil((is_top - hdr['YORGSUBF']) / hdr['YBINNING'])
            hdr['BIASSEC'] = ('[1:%d,1:%d]' % (hdr['NAXIS1'], bottom_binned), c1)

    def list_binnings(self, *args, **kwargs) -> list:
        """List available binnings.

        Returns:
            List of available binnings as (x, y) tuples.
        """

        warnings.warn('The default implementation for list_binnings() in BaseCamera will be removed in future versions',
                      DeprecationWarning)
        return [(1, 1), (2, 2), (3, 3)]


__all__ = ['BaseCamera', 'CameraException']
