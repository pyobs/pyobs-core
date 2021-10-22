import logging
from typing import Union, Any, Dict

from pyobs.object import get_object
from pyobs.images import Image
from pyobs.images.processors.exptime.exptime import ExpTimeEstimator
from pyobs.images.processors.detection import SourceDetection

log = logging.getLogger(__name__)


class StarExpTimeEstimator(ExpTimeEstimator):
    """Estimate exposure time from a star."""
    __module__ = 'pyobs.images.processors.exptime'

    def __init__(self, source_detection: Union[Dict[str, Any], SourceDetection], edge: float = 0.1, bias: float = 0.,
                 saturated: float = 0.7, **kwargs: Any):
        """Create new exp time estimator from single star.

        Args:
            source_detection: Source detection to use.
            edge: Fraction of image to ignore at each border.
            bias: Bias level of image.
            saturated: Fraction of saturation that is used as brightness limit.
        """
        ExpTimeEstimator.__init__(self, **kwargs)

        self._source_detection = source_detection
        self._edge = edge
        self._bias = bias
        self._saturated = saturated
        self.coordinates = (None, None)

    def __call__(self, image: Image) -> Image:
        """Processes an image and stores new exposure time in exp_time attribute.

        Args:
            image: Image to process.

        Returns:
            Original image.
        """

        # get object
        source_detection = get_object(self._source_detection, SourceDetection)

        # do photometry and get copy of catalog
        catalog = source_detection(image).catalog
        if catalog is None:
            log.info('No catalog found in image.')
            return image

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
        self.exp_time = exp_time / (peak - self._bias) * (max_peak - self._bias)
        return image


__all__ = ['StarExpTimeEstimator']
