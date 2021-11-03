import logging
from astropy.wcs import WCS

from pyobs.images import Image
from pyobs.images.processor import ImageProcessor


log = logging.getLogger(__name__)


class Offsets(ImageProcessor):
    """Base class for determining offsets."""
    __module__ = 'pyobs.images.processors.offsets'

    def __call__(self, image: Image) -> Image:
        """Processes an image and sets x/y pixel offset to reference in meta data.

        Args:
            image: Image to process.

        Returns:
            Original image.

        Raises:
            ValueError: If offset could not be found.
        """
        raise NotImplementedError

    @staticmethod
    def on_sky_distance(image: Image) -> float:
        """Calculate on sky distance for offset calculated by any of the derived classes in degrees.

        Args:
            image: Image to analyse. Needs CRPIX1/2 entries in header and 'offsets' in meta.

        Returns:
            On-sky offset of offset in degrees.
        """

        # get central position and offset
        center = image.header['CRPIX1'], image.header['CRPIX2']
        offsets = image.meta['offsets']

        # get WCS
        wcs = WCS(image.header)

        # get RA/Dec at center and at center+offsets
        center_coord = wcs.pixel_to_world(*center)
        offset_coord = wcs.pixel_to_world(*tuple(map(sum, zip(center, offsets))))

        # calculate distance and return it
        return float(center_coord.separation(offset_coord).value)


__all__ = ['Offsets']
