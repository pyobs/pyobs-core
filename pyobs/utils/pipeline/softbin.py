from .pipelinestep import PipelineStep
from pyobs.images import Image


class SoftBinPipelineStep(PipelineStep):
    def __init__(self, binning: int = 2, *args, **kwargs):
        """Init a new software binning pipeline step.

        Args:
            binning: Binning to apply to image.
        """
        self.binning = binning

    def __call__(self, image: Image) -> Image:
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

        # return it
        return image


__all__ = ['SoftBinPipelineStep']
