from typing import List

from .calibration import Image, CalibrationImage


class BiasImage(CalibrationImage):
    @staticmethod
    def create_master(images: List[Image]) -> 'BiasImage':
        # calibrate
        calibrated = [img.calibrate() for img in images]

        # and average
        return BiasImage.combine(calibrated)


__all__ = ['BiasImage']
