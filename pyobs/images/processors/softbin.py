from pyobs.images.processor import ImageProcessor
from pyobs.images import Image


class SoftBin(ImageProcessor):
    def __init__(self, binning: int = 2, *args, **kwargs):
        """Init a new software binning pipeline step.

        Args:
            binning: Binning to apply to image.
        """
        self.binning = binning

    def __call__(self, image: Image):
        """Bin an image.

        Args:
            image: Image to bin.

        Returns:
            Binned image.
        """

        # calculate new shape, in which all binned pixels are in a higher dimension
        shape = (image.data.shape[0] // self.binning, self.binning,
                 image.data.shape[1] // self.binning, self.binning)

        # reshape and average
        image.data = image.data.reshape(shape).mean(-1).mean(1)

        # set NAXIS1/2
        image.header['NAXIS2'], image.header['NAXIS1'] = image.data.shape

        # divide some header entries by binning
        for key in ['CRPIX1', 'CRPIX2']:
            if key in image.header:
                image.header[key] /= self.binning

        # multiply some header entries with binning
        for key in ['DET-BIN1', 'DET-BIN2', 'XBINNING', 'YBINNING', 'CDELT1', 'CDELT2']:
            if key in image.header:
                image.header[key] *= self.binning


__all__ = ['SoftBin']

