from typing import List

from pyobs.utils.images import BiasImage, CalibrationImage, Image


class DarkImage(CalibrationImage):
    @staticmethod
    def create_master(images: List[Image], bias: BiasImage) -> 'DarkImage':
        # calibrate
        calibrated = [img.calibrate(bias=bias) for img in images]

        # divide by exposure time
        data = [img / img.header['EXPTIME'] for img in calibrated]

        # average
        return DarkImage.combine(data)


__all__ = ['DarkImage']
