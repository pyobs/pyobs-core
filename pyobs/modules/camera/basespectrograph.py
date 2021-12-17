import asyncio
import datetime
import logging
from abc import ABCMeta, abstractmethod
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


class BaseSpectrograph(Module, SpectrumFitsHeaderMixin, ISpectrograph, metaclass=ABCMeta):
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
        self._expose_lock = asyncio.Lock()
        self.expose_abort = asyncio.Event()

        # check
        if self.comm is None:
            log.warning('No comm module given, will not be able to signal new images!')

    @abstractmethod
    async def _expose(self, abort_event: asyncio.Event) -> fits.HDUList:
        """Actually do the exposure, should be implemented by derived classes.

        Args:
            abort_event: Event that gets triggered when exposure should be aborted.

        Returns:
            The actual image and, if present, a filename.

        Raises:
            ValueError: If exposure was not successful.
        """
        ...

    async def __expose(self, broadcast: bool) -> Tuple[Optional[fits.HDUList], Optional[str]]:
        """Wrapper for a single exposure.

        Args:
            broadcast: Whether or not the new image should be broadcasted.

        Returns:
            Tuple of the image itself and its filename.

        Raises:
            ValueError: If exposure was not successful.
        """

        # request fits headers
        header_futures_before = await self.request_fits_headers(before=True)

        # do the exposure
        self._exposure = ExposureInfo(start=datetime.datetime.utcnow())
        try:
            hdulist = await self._expose(abort_event=self.expose_abort)
            if hdulist is None or hdulist[0].data is None:
                self._exposure = None
                return None, None
        except:
            # exposure was not successful (aborted?), so reset everything
            self._exposure = None
            raise

        # request fits headers again
        header_futures_after = await self.request_fits_headers(before=False)

        # add HDU name
        hdulist[0].header['EXTNAME'] = 'SCI'

        # add fits headers and format filename
        await self.add_requested_fits_headers(hdulist[0], header_futures_before)
        await self.add_requested_fits_headers(hdulist[0], header_futures_after)
        await self.add_fits_headers(hdulist[0])

        # format filename
        filename = self.format_filename(hdulist[0])

        # don't want to save?
        if filename is None:
            return hdulist, None

        # upload file
        try:
            log.info('Uploading spectrum to file server...')
            await self.vfs.write_fits(filename, hdulist)
        except FileNotFoundError:
            raise ValueError('Could not upload spectrum.')

        # broadcast image path
        if broadcast and self.comm:
            log.info('Broadcasting spectrum ID...')
            await self.comm.send_event(NewSpectrumEvent(filename))

        # return spectrum and unique
        self._exposure = None
        log.info('Finished spectrum %s.', filename)
        return hdulist, filename

    @timeout(10)
    async def grab_spectrum(self, broadcast: bool = True, **kwargs: Any) -> str:
        """Grabs a spectrum and returns reference.

        Args:
            broadcast: Broadcast existence of image.

        Returns:
            Name of image that was taken.
        """

        # are we exposing?
        if self._spectrograph_status != ExposureStatus.IDLE:
            raise ValueError('Cannot start new exposure because spectrograph is not idle.')
        await self._change_exposure_status(ExposureStatus.EXPOSING)

        # expose
        hdu, filename = await self.__expose(broadcast)
        if hdu is None:
            raise ValueError('Could not take spectrum.')
        else:
            if filename is None:
                raise ValueError('Spectrum has not been saved, so cannot be retrieved by filename.')

        # return filename
        await self._change_exposure_status(ExposureStatus.IDLE)
        return filename

    async def _change_exposure_status(self, status: ExposureStatus) -> None:
        """Change exposure status and send event,

        Args:
            status: New exposure status.
        """

        # send event, if it changed
        if self._spectrograph_status != status:
            await self.comm.send_event(ExposureStatusChangedEvent(last=self._spectrograph_status, current=status))

        # set it
        self._spectrograph_status = status

    async def get_exposure_status(self, **kwargs: Any) -> ExposureStatus:
        """Returns the current status of the spectrograph, which is one of 'idle', 'exposing', or 'readout'.

        Returns:
            Current status of spectrograph.
        """
        return self._spectrograph_status

    async def abort(self, **kwargs: Any) -> None:
        """Aborts the current exposure.

        Raises:
            ValueError: If exposure could not be aborted.
        """
        pass


__all__ = ['BaseSpectrograph']
