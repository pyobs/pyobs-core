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

    def __init__(self, masks: Dict[str, Union[np.ndarray, str]], *args, **kwargs):
        """Init an image processor that adds a mask to an image.

        Args:
            masks: Dictionary containing binning->mask.
        """

        # masks
        self._masks = {}
        if masks is not None:
            for binning, mask in masks.items():
                if isinstance(mask, np.ndarray):
                    self._masks[binning] = mask
                elif isinstance(mask, str):
                    self._masks[binning] = fits.getdata(mask)
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
        binning = '%dx%s' % (image.header['XBINNING'], image.header['YBINNING'])
        if binning in self._masks:
            img.mask = self._masks[binning].copy()
        else:
            log.warning('No mask found for binning of frame.')

        # finished
        return img


__all__ = ['AddMask']

