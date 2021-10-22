import logging

from pyobs.images.processor import ImageProcessor
from pyobs.images import Image


log = logging.getLogger(__name__)


class SoftBin(ImageProcessor):
    """Bin an image."""
    __module__ = 'pyobs.images.processors.misc'

    def __init__(self, binning: int = 2, **kwargs:: Any):
        """Init a new software binning pipeline step.

        Args:
            binning: Binning to apply to image.
        """
        ImageProcessor.__init__(self, **kwargs)

        # store
        self.binning = binning

    def __call__(self, image: Image) -> Image:
        """Bin an image.

        Args:
            image: Image to bin.

        Returns:
            Binned image.
        """

        # copy image
        img = image.copy()
        if img.data is None:
            log.warning('No data found in image.')
            return image

        # calculate new shape, in which all binned pixels are in a higher dimension
        shape = (img.data.shape[0] // self.binning, self.binning,
                 img.data.shape[1] // self.binning, self.binning)

        # reshape and average
        img.data = img.data.reshape(shape).mean(-1).mean(1)
        if img.data is None:
            log.warning('No data found in image after reshaping.')
            return image

        # set NAXIS1/2
        img.header['NAXIS2'], img.header['NAXIS1'] = img.data.shape

        # divide some header entries by binning
        for key in ['CRPIX1', 'CRPIX2']:
            if key in img.header:
                img.header[key] /= self.binning

        # multiply some header entries with binning
        for key in ['DET-BIN1', 'DET-BIN2', 'XBINNING', 'YBINNING', 'CDELT1', 'CDELT2']:
            if key in img.header:
                img.header[key] *= self.binning

        # return result
        return img


__all__ = ['SoftBin']

