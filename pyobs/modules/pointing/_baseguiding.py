from typing import Union, List, Dict, Tuple, Any, Optional
import logging
from astropy.coordinates import SkyCoord
import astropy.units as u

from pyobs.utils.time import Time
from pyobs.interfaces import IAutoGuiding, IFitsHeaderProvider
from pyobs.images import Image
from ._base import BasePointing
from ...interfaces.proxies import ITelescopeProxy

log = logging.getLogger(__name__)


class BaseGuiding(BasePointing, IAutoGuiding, IFitsHeaderProvider):
    """Base class for guiding modules."""
    __module__ = 'pyobs.modules.pointing'

    def __init__(self, max_exposure_time: Optional[float] = None, min_interval: float = 0, max_interval: float = 600,
                 separation_reset: Optional[float] = None, pid: bool = False, **kwargs: Any):
        """Initializes a new science frame auto guiding system.

        Args:
            max_exposure_time: Maximum exposure time in sec for images to analyse.
            min_interval: Minimum interval in sec between two images.
            max_interval: Maximum interval in sec between to consecutive images to guide.
            separation_reset: Min separation in arcsec between two consecutive images that triggers a reset.
            pid: Whether to use a PID for guiding.
        """
        BasePointing.__init__(self, **kwargs)

        # store
        self._enabled = False
        self._max_exposure_time = max_exposure_time
        self._min_interval = min_interval
        self._max_interval = max_interval
        self._separation_reset = separation_reset
        self._pid = pid
        self._loop_closed = False

        # headers of last and of reference image
        self._last_header = None
        self._ref_header = None

    def start(self, **kwargs: Any) -> None:
        """Starts/resets auto-guiding."""
        log.info('Start auto-guiding...')
        self._reset_guiding(enabled=True)

    def stop(self, **kwargs: Any) -> None:
        """Stops auto-guiding."""
        log.info('Stopping autp-guiding...')
        self._reset_guiding(enabled=False)

    def is_running(self, **kwargs: Any) -> bool:
        """Whether auto-guiding is running.

        Returns:
            Auto-guiding is running.
        """
        return self._enabled

    def get_fits_headers(self, namespaces: Optional[List[str]] = None, **kwargs: Any) -> Dict[str, Tuple[Any, str]]:
        """Returns FITS header for the current status of this module.

        Args:
            namespaces: If given, only return FITS headers for the given namespaces.

        Returns:
            Dictionary containing FITS headers.
        """

        # state
        state = 'GUIDING_CLOSED_LOOP' if self._loop_closed else 'GUIDING_OPEN_LOOP'

        # return header
        return {
            'AGSTATE': (state, 'Autoguider state')
        }

    def _reset_guiding(self, enabled: bool = True, image: Optional[Union[Image, None]] = None) -> None:
        """Reset guiding.

        Args:
            image: If given, new reference image.
        """
        self._enabled = enabled
        self._loop_closed = False
        self._ref_header = None if image is None else image.header
        self._last_header = None if image is None else image.header

        # reset offset
        self.reset_pipeline()
        if image is not None:
            # if image is given, process it
            self.run_pipeline(image)

    def _process_image(self, image: Image) -> Optional[Image]:
        """Processes a single image and offsets telescope.

        Args:
            image: Image to process.
        """

        # not enabled?
        if not self._enabled:
            return None

        # we only accept OBJECT images
        if image.header['IMAGETYP'] != 'object':
            return None

        # reference header?
        if self._ref_header is None:
            log.info('Setting new reference image...')
            self._reset_guiding(image=image)
            return None

        # check RA/Dec in header and separation
        c1 = SkyCoord(ra=image.header['TEL-RA'] * u.deg, dec=image.header['TEL-DEC'] * u.deg, frame='icrs')
        c2 = SkyCoord(ra=self._ref_header['TEL-RA'] * u.deg, dec=self._ref_header['TEL-DEC'] * u.deg, frame='icrs')
        separation = c1.separation(c2).deg
        if self._separation_reset is not None and separation * 3600. > self._separation_reset:
            log.warning('Nominal position of reference and new image differ by %.2f", resetting reference...',
                            separation * 3600.)
            self._reset_guiding(image=image)
            return None

        # check filter
        if 'FILTER' in image.header and 'FILTER' in self._ref_header and \
                image.header['FILTER'] != self._ref_header['FILTER']:
            log.warning('The filter has been changed since the last exposure, resetting reference...')
            self._reset_guiding(image=image)
            return None

        # get time
        date_obs = Time(image.header['DATE-OBS'])

        # check times and focus
        if self._last_header is not None:
            # check times
            t0 = Time(self._last_header['DATE-OBS'])
            if (date_obs - t0).sec > self._max_interval:
                log.warning('Time between current and last image is too large, resetting reference...')
                self._reset_guiding(image=image)
                return None
            if (date_obs - t0).sec < self._min_interval:
                log.warning('Time between current and last image is too small, ignoring image...')
                return None

            # check focus
            if 'TEL-FOCU' in image.header:
                if abs(image.header['TEL-FOCU'] - self._last_header['TEL-FOCU']) > 0.05:
                    log.warning('Focus difference between current and last image is too large, resetting reference...')
                    self._reset_guiding(image=image)
                    return None

        # exposure time too large?
        if self._max_exposure_time is not None and image.header['EXPTIME'] > self._max_exposure_time:
            log.warning('Exposure time too large, skipping auto-guiding for now...')
            return None

        # remember header
        self._last_header = image.header

        # get offset
        image = self.run_pipeline(image)

        # get telescope
        try:
            telescope: ITelescopeProxy = self.proxy(self._telescope, ITelescopeProxy)
        except ValueError:
            log.error('Given telescope does not exist or is not of correct type.')
            return image

        # apply offsets
        if self._apply(image, telescope, self.location):
            log.info('Finished image.')
        else:
            log.warning('Could not apply offsets.')

        # return image, in case we added important data
        return image


__all__ = ['BaseGuiding']
