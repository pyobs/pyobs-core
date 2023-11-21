from typing import Optional

from astropy.nddata import CCDData

from pyobs.images import Image
from pyobs.utils.pipeline import Pipeline

import astropy.units as u


class _CCDDataCalibrator:
    def __init__(self, image: Image, bias: Image = None, dark: Image = None, flat: Image = None):
        self._image = image
        self._bias = self._optional_to_ccddata(bias)
        self._dark = self._optional_to_ccddata(dark)
        self._flat = self._optional_to_ccddata(flat)

        self._ccd_data = image.to_ccddata()

        if dark is not None:
            self._dark_exp_time = dark.header["EXPTIME"]

    @staticmethod
    def _optional_to_ccddata(image: Optional[Image]) -> Optional[CCDData]:
        if image is None:
            return None
        return image.to_ccddata()

    def __call__(self) -> Image:
        self._trim_image()

        calibrated_ccd_data = self._calibrate_image()

        calibrated = Image.from_ccddata(calibrated_ccd_data)
        return calibrated

    def _trim_image(self):
        self._ccd_data = Pipeline.trim_ccddata(self._ccd_data)

    def _calibrate_image(self):
        import ccdproc

        return ccdproc.ccd_process(
            self._ccd_data,
            error=True,
            master_bias=self._bias,
            dark_frame=self._dark,
            master_flat=self._flat,
            bad_pixel_mask=None,
            gain=self._image.header["DET-GAIN"] * u.electron / u.adu,
            readnoise=self._image.header["DET-RON"] * u.electron,
            dark_exposure=self._dark_exp_time * u.second if self._dark is not None else None,
            data_exposure=self._image.header["EXPTIME"] * u.second,
            dark_scale=True,
            gain_corrected=False,
        )
