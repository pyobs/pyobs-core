import datetime
import logging
import threading
from typing import Tuple, Optional, Dict, Any, NamedTuple, List
from astropy.io import fits

from pyobs.mixins.fitsheader import SpectrumFitsHeaderMixin
from pyobs.utils.enums import ExposureStatus
from pyobs.modules import Module
from pyobs.events import NewSpectrumEvent, ExposureStatusChangedEvent
from pyobs.interfaces import ISpectrograph
from pyobs.modules import timeout

log = logging.getLogger(__name__)


class ExposureInfo(NamedTuple):
    """Info about a running exposure."""
    start: datetime.datetime


class BaseSpectrograph(Module, SpectrumFitsHeaderMixin, ISpectrograph):
    """Base class for all spectrograph modules."""
    __module__ = 'pyobs.modules.camera'

    def __init__(self, fits_headers: Optional[Dict[str, Any]] = None,
                 filenames: str = '/cache/pyobs-{DAY-OBS|date:}-{FRAMENUM|string:04d}.fits.gz',
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

        # init camera
        self._exposure: Optional[ExposureInfo] = None
        self._spectrograph_status = ExposureStatus.IDLE

        # multi-threading
        self._expose_lock = threading.Lock()
        self.expose_abort = threading.Event()

        # check
        if self.comm is None:
            log.warning('No comm module given, will not be able to signal new images!')

    def _expose(self, abort_event: threading.Event) -> fits.PrimaryHDU:
        """Actually do the exposure, should be implemented by derived classes.

        Args:
            abort_event: Event that gets triggered when exposure should be aborted.

        Returns:
            The actual image.

        Raises:
            ValueError: If exposure was not successful.
        """
        raise NotImplementedError

    def __expose(self, broadcast: bool) -> Tuple[Optional[fits.PrimaryHDU], Optional[str]]:
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

        # do the exposure
        self._exposure = ExposureInfo(start=datetime.datetime.utcnow())
        try:
            spectrum = self._expose(abort_event=self.expose_abort)
            if spectrum is None or spectrum.data is None:
                self._exposure = None
                return None, None
        except:
            # exposure was not successful (aborted?), so reset everything
            self._exposure = None
            raise

        # request fits headers again
        header_futures_after = self.request_fits_headers(before=False)

        # add HDU name
        spectrum.header['EXTNAME'] = 'SCI'

        # add fits headers and format filename
        self.add_requested_fits_headers(spectrum, header_futures_before)
        self.add_requested_fits_headers(spectrum, header_futures_after)
        self.add_fits_headers(spectrum)
        filename = self.format_filename(spectrum)

        # don't want to save?
        if filename is None:
            return spectrum, None

        # upload file
        try:
            log.info('Uploading spectrum to file server...')
            self.vfs.write_fits(filename, fits.HDUList([spectrum]))
        except FileNotFoundError:
            raise ValueError('Could not upload spectrum.')

        # broadcast image path
        if broadcast and self.comm:
            log.info('Broadcasting spectrum ID...')
            self.comm.send_event(NewSpectrumEvent(filename))

        # return spectrum and unique
        self._exposure = None
        log.info('Finished spectrum %s.', filename)
        return spectrum, filename

    @timeout(10)
    def grab_spectrum(self, broadcast: bool = True, **kwargs: Any) -> str:
        """Grabs a spectrum and returns reference.

        Args:
            broadcast: Broadcast existence of image.

        Returns:
            Name of image that was taken.
        """
        # acquire lock
        log.info('Acquiring exclusive lock on spectrograph...')
        if not self._expose_lock.acquire(blocking=False):
            raise ValueError('Could not acquire spectrograph lock for grab_spectrum().')

        # make sure that we release the lock
        try:
            # are we exposing?
            if self._spectrograph_status != ExposureStatus.IDLE:
                raise ValueError('Cannot start new exposure because spectrograph is not idle.')

            # expose
            hdu, filename = self.__expose(broadcast)
            if hdu is None:
                raise ValueError('Could not take spectrum.')
            else:
                if filename is None:
                    raise ValueError('Spectrum has not been saved, so cannot be retrieved by filename.')

            # return filename
            return filename

        finally:
            # release lock
            log.info('Releasing exclusive lock on spectrograph...')
            self._expose_lock.release()

    def _change_exposure_status(self, status: ExposureStatus) -> None:
        """Change exposure status and send event,

        Args:
            status: New exposure status.
        """

        # send event, if it changed
        if self._spectrograph_status != status:
            self.comm.send_event(ExposureStatusChangedEvent(last=self._spectrograph_status, current=status))

        # set it
        self._spectrograph_status = status

    def get_exposure_status(self, **kwargs: Any) -> ExposureStatus:
        """Returns the current status of the spectrograph, which is one of 'idle', 'exposing', or 'readout'.

        Returns:
            Current status of spectrograph.
        """
        return self._spectrograph_status


__all__ = ['BaseSpectrograph']
