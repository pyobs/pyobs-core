from typing import Union, Dict
import logging
import numpy as np
from astropy.io import fits

from pyobs.images.processor import ImageProcessor
from pyobs.images import Image


log = logging.getLogger(__name__)


class AddMask(ImageProcessor):
    """Add mask to image."""
    __module__ = 'pyobs.images.processors.misc'

    def __init__(self, masks: Dict[str, Dict[str, Union[np.ndarray, str]]], **kwargs: Any):
        """Init an image processor that adds a mask to an image.

        Args:
            masks: Dictionary containing instrument->binning->mask, with binning as string, e.g. '1x1'.
        """
        ImageProcessor.__init__(self, **kwargs)

        # masks
        self._masks: Dict[str, Dict[str, np.ndarray]] = {}
        for instrument, group in masks.items():
            self._masks[instrument] = {}
            for binning, mask in group.items():
                if isinstance(mask, np.ndarray):
                    self._masks[instrument][binning] = mask
                elif isinstance(mask, str):
                    self._masks[instrument][binning] = fits.getdata(mask)
                else:
                    raise ValueError('Unknown mask format.')

    def __call__(self, image: Image) -> Image:
        """Add mask to image.

        Args:
            image: Image to add mask to.

        Returns:
            Image with mask
        """

        # copy image
        img = image.copy()

        # add mask
        instrument = image.header['INSTRUME']
        binning = '%dx%s' % (image.header['XBINNING'], image.header['YBINNING'])
        if binning in self._masks:
            img.mask = self._masks[instrument][binning].copy()
        else:
            log.warning('No mask found for binning of frame.')

        # finished
        return img


__all__ = ['AddMask']

