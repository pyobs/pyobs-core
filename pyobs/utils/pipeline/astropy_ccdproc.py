import logging
from typing import Union, Dict, List
import ccdproc
import numpy as np
import astropy.units as u

from pyobs.object import get_object
from pyobs.utils.fits import FilenameFormatter
from pyobs.images import Image
from pyobs.images.processors.astrometry import Astrometry
from pyobs.images.processors.photometry import Photometry
from pyobs.images.processors.detection import SourceDetection
from .pipeline import Pipeline

log = logging.getLogger(__name__)


class ccdprocPipeline(Pipeline):
    """Pipeline based on the astropy package ccdproc."""

    def __init__(self, source_detection: Union[dict, SourceDetection] = None,
                 photometry: Union[dict, Photometry] = None, astrometry: Union[dict, Astrometry] = None,
                 masks: Dict[str, Union[Image, str]] = None, filenames: str = None, *args, **kwargs):
        """Pipeline for science images.

        Args:
            source_detection: SourceDetection object. If None, no detection is performed.
            photometry: Photometry object. If None, no photometry is performed.
            astrometry: Astrometry object. If None, no astrometry is performed.
            masks: Dictionary with masks to use for each binning given as, e.g., 1x1.
            *args:
            **kwargs:
        """

        # get objects
        self._source_detection = None if source_detection is None else get_object(source_detection, SourceDetection)
        self._photometry = None if photometry is None else get_object(photometry, Photometry)
        self._astrometry = None if astrometry is None else get_object(astrometry, Astrometry)

        # masks
        self._masks = {}
        if masks is not None:
            for binning, mask in masks.items():
                if isinstance(mask, Image):
                    self._masks[binning] = mask
                elif isinstance(mask, str):
                    self._masks[binning] = Image.from_file(mask)
                else:
                    raise ValueError('Unknown mask format.')

        # default filename patterns
        if filenames is None:
            filenames = '{SITEID}{TELID}-{INSTRUME}-{DAY-OBS|date:}-{FRAMENUM|string:04d}-{IMAGETYP|type}01.fits'
        self._formatter = FilenameFormatter(filenames)

    def _combine_calib_images(self, images: List[Image], bias: Image = None, normalize: bool = False,
                              method: str = 'average'):
        """Combine a list of given images.

        Args:
            images: List of images to combine.
            bias: If given, subtract from images before combining them.
            normalize: If True, images are normalized to median of 1 before and after combining them.
            method: Method for combining images.
        """

        # get CCDData objects
        data = [image.to_ccddata() for image in images]

        # subtract bias?
        if bias is not None:
            bias_data = bias.to_ccddata()
            data = [ccdproc.subtract_bias(d, bias_data) for d in data]

        # normalize?
        if normalize:
            data = [d.divide(np.median(d.data), handle_meta='first_found') for d in data]

        # combine image
        combined = ccdproc.combine(data, method=method,
                                   sigma_clip=True, sigma_clip_low_thresh=5, sigma_clip_high_thresh=5,
                                   mem_limit=350e6, unit='adu',
                                   combine_uncertainty_function=np.ma.std)

        # normalize?
        if normalize:
            combined = combined.divide(np.median(combined.data), handle_meta='first_found')

        # to Image and copy header
        image = Image.from_ccddata(combined)

        # add history
        for i, src in enumerate(images, 1):
            basename = src.header['FNAME'].replace('.fits.fz', '').replace('.fits', '')
            image.header['L1AVG%03d' % i] = (basename, 'Image used for average')
        image.header['RLEVEL'] = (1, 'Reduction level')

        # finished
        return image

    def create_master_bias(self, images: List[Image]) -> Image:
        """Create master bias frame.

        Args:
            images: List of raw bias frames.

        Returns:
            Master bias frame.
        """
        return self._combine_calib_images(images)

    def create_master_dark(self, images: List[Image], bias: Image) -> Image:
        """Create master dark frame.

        Args:
            images: List of raw dark frames.
            bias: Bias frame to subtract from images.

        Returns:
            Master dark frame.
        """
        return self._combine_calib_images(images, bias=bias)

    def create_master_flat(self, images: List[Image], bias: Image) -> Image:
        """Create master flat frame.

        Args:
            images: List of raw flat frames.
            bias: Bias frame to subtract from images.

        Returns:
            Master flat frame.
        """
        return self._combine_calib_images(images, bias=bias, normalize=True, method='median')

    def calibrate(self, image: Image, bias: Image = None, dark: Image = None, flat: Image = None) -> Image:
        """Calibrate a single science frame.

        Args:
            image: Image to calibrate.
            bias: Bias frame to use.
            dark: Dark frame to use.
            flat: Flat frame to use.

        Returns:
            Calibrated image.
        """

        # calibrate image
        calibrated = ccdproc.ccd_process(image.to_ccddata(),
                                         oscan=image.header['BIASSEC'] if 'BIASSEC' in image.header else None,
                                         trim=image.header['TRIMSEC'] if 'TRIMSEC' in image.header else None,
                                         error=True,
                                         master_bias=None if bias is None else bias.to_ccddata(),
                                         dark_frame=None if dark is None else dark.to_ccddata(),
                                         master_flat=None if flat is None else flat.to_ccddata(),
                                         bad_pixel_mask=None,
                                         gain=image.header['det-gain'] * u.electron / u.adu,
                                         readnoise=image.header['det-ron'] * u.electron,
                                         dark_exposure=None if dark is None else dark.header['exptime'] * u.second,
                                         data_exposure=image.header['exptime'] * u.second,
                                         dark_scale=True,
                                         gain_corrected=False)

        # to image
        calibrated = Image.from_ccddata(calibrated)
        calibrated.header['BUNIT'] = ('electron', 'Unit of pixel values')

        # add mask
        binning = '%dx%s' % (image.header['XBINNING'], image.header['YBINNING'])
        if binning in self._masks:
            calibrated.mask = self._masks[binning].copy()
        else:
            log.warning('No mask found for binning of frame.')

        # set (raw) filename
        calibrated.format_filename(self._formatter)
        if 'ORIGNAME' in image.header:
            calibrated.header['L1RAW'] = image.header['ORIGNAME']

        # search stars and do photometry and astrometry
        if self._source_detection is not None:
            # find stars
            self._source_detection(calibrated)

            if self._photometry is not None:
                # find stars
                self._photometry(calibrated)

                # do astrometry
                if self._astrometry is not None:
                    try:
                        self._astrometry(calibrated)
                    except ValueError:
                        # error message comes from astrometry
                        pass

        # return calibrated image
        return calibrated


__all__ = ['ccdprocPipeline']
