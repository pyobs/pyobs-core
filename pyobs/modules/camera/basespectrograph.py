import datetime
import logging
import threading
import warnings
from typing import Tuple, Optional, Dict, Any, NamedTuple, List
import numpy as np
from astropy.io import fits
from numpy.typing import NDArray

from pyobs.mixins.fitsheader import ImageFitsHeaderMixin, SpectrumFitsHeaderMixin
from pyobs.utils.enums import ImageType, ExposureStatus
from pyobs.images import Image
from pyobs.modules import Module
from pyobs.events import NewImageEvent, ExposureStatusChangedEvent
from pyobs.interfaces import ICamera, IExposureTime, IImageType, ISpectrograph
from pyobs.modules import timeout

log = logging.getLogger(__name__)


class BaseSpectrograph(Module, SpectrumFitsHeaderMixin, ISpectrograph):
    """Base class for all spectrograph modules."""
    __module__ = 'pyobs.modules.camera'

    def __init__(self, fits_headers: Optional[Dict[str, Any]] = None,
                 filenames: str = '/cache/pyobs-{DAY-OBS|date:}-{FRAMENUM|string:04d}-{IMAGETYP|type}00.fits.gz',
                 fits_namespaces: Optional[List[str]] = None, **kwargs: Any):
        """Creates a new BaseCamera.

        Args:
            fits_headers: Additional FITS headers.
            flip: Whether or not to flip the image along its first axis.
            filenames: Template for file naming.
            fits_namespaces: List of namespaces for FITS headers that this camera should request
        """
        Module.__init__(self, **kwargs)
        SpectrumFitsHeaderMixin.__init__(self, fits_namespaces=fits_namespaces, fits_headers=fits_headers,
                                         filenames=filenames)

        # check
        if self.comm is None:
            log.warning('No comm module given, will not be able to signal new images!')

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
        header_futures_before = self.request_fits_headers(before=True)

        # open the shutter?
        open_shutter = image_type not in [ImageType.BIAS, ImageType.DARK]

        # do the exposure
        self._exposure = ExposureInfo(start=datetime.datetime.utcnow(), exposure_time=exposure_time)
        try:
            image = self._expose(exposure_time, open_shutter, abort_event=self.expose_abort)
            if image is None or image.data is None:
                self._exposure = None
                return None, None
        except:
            # exposure was not successful (aborted?), so reset everything
            self._exposure = None
            raise

        # request fits headers again
        header_futures_after = self.request_fits_headers(before=False)

        # flip it?
        if self._flip:
            # do we have three dimensions in array? need this for deciding which axis to flip
            is_3d = len(image.data.shape) == 3

            # flip image and make contiguous again
            flipped: NDArray[Any] = np.flip(image.data, axis=1 if is_3d else 0)  # type: ignore
            image.data = np.ascontiguousarray(flipped)

        # add HDU name
        image.header['EXTNAME'] = 'SCI'

        # add image type
        image.header['IMAGETYP'] = image_type.value

        # add fits headers and format filename
        self.add_requested_fits_headers(image, header_futures_before)
        self.add_requested_fits_headers(image, header_futures_after)
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

    @timeout(10)
    def grab_image(self, broadcast: bool = True, **kwargs: Any) -> str:
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


__all__ = ['BaseSpectrograph']
