from typing import List, Type, Union
import numpy as np
from astropy.stats import sigma_clip
import astropy.units as u
import logging

from pyobs.interfaces import ICamera
from pyobs.utils.time import Time
from .image import Image
from pyobs.utils.archive import FrameInfo
from pyobs.utils.enums import ImageType

log = logging.getLogger(__name__)


class CalibrationImage(Image):
    @staticmethod
    def combine(images: List[Image], method: Image.CombineMethod = Image.CombineMethod.MEAN):
        """Combines images into a single one.

        Args:
            images: Images to combine.
            method: Method to use for combination.

        Returns:
            Combined image.
        """

        # collect data
        data = [img.data for img in images]

        # create new image
        img = Image()

        # average
        if method == Image.CombineMethod.MEAN:
            img.data = np.mean(data, axis=0)
        elif method == Image.CombineMethod.MEDIAN:
            img.data = np.median(data, axis=0)
        elif method == Image.CombineMethod.SIGMA:
            tmp = sigma_clip(data, axis=0)
            img.data = np.mean(tmp, axis=0)
        else:
            raise ValueError('Unknown combine method.')

        # header
        img.header = images[0].header.copy()

        # add history
        for i, src in enumerate(images, 1):
            basename = src.header['FNAME'].replace('.fits.fz', '').replace('.fits', '')
            img.header['L1AVG%03d' % i] = (basename, 'Image used for average')
        img.header['RLEVEL'] = (1, 'Reduction level')

        # finished
        return img


__all__ = ['CalibrationImage']
