from typing import List
import numpy as np

from pyobs.utils.images import BiasImage, DarkImage, CalibrationImage, Image


class FlatImage(CalibrationImage):
    @staticmethod
    def create_master(images: List[Image], bias: BiasImage, dark: DarkImage,
                      method: Image.CombineMethod = Image.CombineMethod.MEAN) -> 'DarkImage':
        # calibrate
        calibrated = [img.calibrate(bias=bias, dark=dark) for img in images]

        # normalize to mean
        for img in calibrated:
            img.data /= np.mean(img.data)

        # average
        average = FlatImage.combine(calibrated, method=method)

        # divide flat by its mean
        average.data /= np.mean(average.data)

        # finished
        return average


__all__ = ['FlatImage']
