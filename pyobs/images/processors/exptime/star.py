import logging
from typing import Union

from pyobs import get_object
from pyobs.images import Image
from pyobs.images.processors.exptime.exptime import ExpTimeEstimator
from pyobs.images.processors.photometry import Photometry

log = logging.getLogger(__name__)


class StarExpTimeEstimator(ExpTimeEstimator):
    def __init__(self, photometry: Union[dict, Photometry], edge: float = 0.1, bias: float = 0., saturated: float = 0.7,
                 *args, **kwargs):
        """Create new exp time estimator from single star.

        Args:
            photometry: Photometry to use.
            edge: Fraction of image to ignore at each border.
            bias: Bias level of image.
            saturated: Fraction of saturation that is used as brightness limit.
        """
        self._photometry = photometry
        self._edge = edge
        self._bias = bias
        self._saturated = saturated
        self.coordinates = (None, None)

    def __call__(self, image: Image) -> float:
        """Processes an image and returns a new best exposure time in seconds.

        Args:
            image: Image to process.

        Returns:
            New best exposure time in seconds.
        """

        # get object
        photometry = get_object(self._photometry, Photometry)

        # do photometry and get copy of catalog
        catalog = photometry(image).copy(True)

        # sort catalog by peak flux
        catalog.sort('peak')

        # saturation level
        if 'DET-SATU' in image.header and 'DET-GAIN' in image.header:
            saturation = image.header['DET-SATU'] / image.header['DET-GAIN']
        else:
            saturation = 50000

        # get max peak flux that we allow
        max_peak = saturation * self._saturated

        # filter out all stars that are saturated
        catalog = catalog[catalog['peak'] <= max_peak]

        # get brightest star, get its peak flux and store its coordinates
        star = catalog[0]
        peak = star['peak']
        log.info('Found peak of %.2f at %.1fx%.1f.', star['peak'], star['x'], star['y'])
        self.coordinates = (star['x'], star['y'])

        # get exposure time of image
        exp_time = image.header['EXPTIME']

        # calculate new exposure time and return it
        new_exp_time = exp_time / (peak - self._bias) * (max_peak - self._bias)
        return new_exp_time


__all__ = ['StarExpTimeEstimator']
