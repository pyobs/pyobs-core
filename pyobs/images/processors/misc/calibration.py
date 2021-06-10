import multiprocessing
import threading
from typing import Union, Optional, List, Tuple
import logging
import astropy.units as u
import ccdproc

from pyobs.images.processor import ImageProcessor
from pyobs.images import Image
from pyobs.object import get_object
from pyobs.utils.archive import Archive
from pyobs.utils.enums import ImageType
from pyobs.utils.pipeline import Pipeline
from pyobs.utils.time import Time


log = logging.getLogger(__name__)


class Calibration(ImageProcessor):
    """Calibrate an image."""
    __module__ = 'pyobs.images.processors.misc'

    """Cache for calibration frames."""
    calib_cache: List[Tuple[Tuple[ImageType, str, str, Optional[str]], Image]] = []

    def __init__(self, archive: Union[dict, Archive], max_cache_size: int = 20, *args, **kwargs):
        """Init a new image calibration pipeline step.

        Args:
            archive: Archive to fetch calibration frames from.
        """

        # store
        self._max_cache_size = max_cache_size

        # get archive
        self._archive = get_object(archive, Archive)

    def __call__(self, image: Image) -> Image:
        """Calibrate an image.

        Args:
            image: Image to calibrate.

        Returns:
            Calibrated image.
        """

        # get calibration masters
        try:
            bias = self._find_master(image, ImageType.BIAS)
            dark = self._find_master(image, ImageType.DARK)
            flat = self._find_master(image, ImageType.SKYFLAT)
        except ValueError as e:
            log.error('Could not find calibration frames: ' + str(e))
            return image

        # calibrate image
        calibrated = ccdproc.ccd_process(image.to_ccddata(),
                                         oscan=image.header['BIASSEC'] if 'BIASSEC' in image.header else None,
                                         trim=image.header['TRIMSEC'] if 'TRIMSEC' in image.header else None,
                                         error=True,
                                         master_bias=bias.to_ccddata(),
                                         dark_frame=dark.to_ccddata(),
                                         master_flat=flat.to_ccddata(),
                                         bad_pixel_mask=None,
                                         gain=image.header['DET-GAIN'] * u.electron / u.adu,
                                         readnoise=image.header['DET-RON'] * u.electron,
                                         dark_exposure=dark.header['EXPTIME'] * u.second,
                                         data_exposure=image.header['EXPTIME'] * u.second,
                                         dark_scale=True,
                                         gain_corrected=False)

        # to image
        calibrated = Image.from_ccddata(calibrated)
        calibrated.header['BUNIT'] = ('electron', 'Unit of pixel values')

        # set raw filename
        if 'ORIGNAME' in image.header:
            calibrated.header['L1RAW'] = image.header['ORIGNAME'].replace('.fits', '')

        # add calibration frames
        calibrated.header['L1BIAS'] = (bias.header['FNAME'].replace('.fits.fz', '').replace('.fits', ''),
                                       'Name of BIAS frame')
        calibrated.header['L1DARK'] = (dark.header['FNAME'].replace('.fits.fz', '').replace('.fits', ''),
                                       'Name of DARK frame')
        calibrated.header['L1FLAT'] = (flat.header['FNAME'].replace('.fits.fz', '').replace('.fits', ''),
                                       'Name of FLAT frame')

        # set RLEVEL
        calibrated.header['RLEVEL'] = (1, 'Reduction level')

        # finished
        return calibrated

    def _find_master(self, image: Image, image_type: ImageType) -> Optional[Image]:
        """Find master calibration frame for given parameters using a cache.

        Args:
            image_type: image type.
            instrument: Instrument name.
            binning: Binning.
            filter_name: Name of filter.
            max_days: Maximum number of days from DATE-OBS to find frames.

        Returns:
            Image or None

        Raises:
            ValueError: if no calibration frame could be found.
        """

        # get mode
        try:
            instrument = image.header['INSTRUME']
            binning = '{0}x{0}'.format(image.header['XBINNING'])
            filter_name = image.header['FILTER'] if 'FILTER' in image.header else None
            time = Time(image.header['DATE-OBS'])
            mode = image_type, instrument, binning, filter_name
        except KeyError:
            # could not fetch header items
            raise ValueError('Could not fetch items from image header.')

        # is in cache?
        for m, item in Calibration.calib_cache:
            if m == mode:
                return item
        print('CACHE MISS:', instrument, binning, filter_name, image_type)
        print('CACHE: ', multiprocessing.current_process(), [c[0] for c in Calibration.calib_cache])

        # try to download one
        master = Pipeline.find_master(self._archive, image_type, time, instrument, binning, filter_name, max_days=30)

        # nothing?
        if master is None:
            raise ValueError('No master frame found.')

        # store it in cache
        Calibration.calib_cache.append((mode, master))

        # too many entries?
        while len(Calibration.calib_cache) > self._max_cache_size:
            Calibration.calib_cache.pop(0)

        # return it
        return master


__all__ = ['Calibration']

