from __future__ import annotations

import astropy.units as u
from astropy.nddata import CCDData

from pyobs.images import Image


class _CCDDataCalibrator:
    def __init__(
        self,
        image: Image,
        bias: Image | None = None,
        dark: Image | None = None,
        flat: Image | None = None,
        dark_scale: bool = True,
    ):
        # to_ccddata() below never carries a catalog through anyway, so drop it before trim() to
        # avoid its stale-catalog guard rejecting an image whose catalog wouldn't survive regardless.
        if image.safe_catalog is not None:
            image = image.copy()
            image.catalog = None
        self._image = image.trim()
        self._bias = self._optional_to_ccddata(bias)
        self._dark = self._optional_to_ccddata(dark)
        self._flat = self._optional_to_ccddata(flat)
        # whether ccd_process() should rescale the dark to the science exptime -- False for an
        # exact exptime-match master, which is used as-is (see Calibration._find_dark_master).
        self._dark_scale = dark_scale

        self._ccd_data = self._image.to_ccddata()

        if dark is not None:
            self._dark_exp_time = dark.header["EXPTIME"]

    @staticmethod
    def _optional_to_ccddata(image: Image | None) -> CCDData | None:
        if image is None:
            return None
        return image.to_ccddata()

    def __call__(self) -> Image:
        calibrated_ccd_data = self._calibrate_image()

        calibrated = Image.from_ccddata(calibrated_ccd_data)
        return calibrated

    def _calibrate_image(self) -> CCDData:
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
            dark_exposure=self._dark_exp_time * u.second if (self._dark is not None and self._dark_scale) else None,
            data_exposure=self._image.header["EXPTIME"] * u.second,
            dark_scale=self._dark_scale,
            gain_corrected=False,
        )
