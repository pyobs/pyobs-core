from typing import List
import numpy as np

from pyobs.utils.images import BiasImage, DarkImage, CalibrationImage, Image


class FlatImage(CalibrationImage):
    @staticmethod
    def create_master(images: List[Image], bias: BiasImage, dark: DarkImage) -> 'DarkImage':
        # calibrate
        calibrated = [img.calibrate(bias=bias, dark=dark) for img in images]

        # average
        average = FlatImage.average(calibrated)

        # divide flat by its mean
        average.data /= np.mean(average.data)

        # finished
        return average


__all__ = ['FlatImage']
