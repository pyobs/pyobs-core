"""The FITS header cards that every camera frame gets, shared by the camera modules and the local camera GUIs.

Lives outside of ``pyobs.utils.gui`` on purpose: that package imports Qt, which a camera module must not need.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import numpy as np
from astropy.io import fits
from numpy.typing import NDArray


@dataclass(frozen=True, kw_only=True)
class FrameSettings:
    """What a driver knows about a frame. Everything that is None is left out of the header.

    Attributes:
        date_obs: Start of the exposure, UTC. A datetime or an ISO string.
        exposure_time: Exposure time in seconds.
        instrument: Name of the instrument.
        binning: Binning in x and y. Leave it out if the camera does not tell.
        window: Left, top, width and height of the window in unbinned pixels. Only left and top go into the header.
        pixel_size: Size of the (square) detector pixels in mm, unbinned.
        gain: Gain setting used for the exposure.
        offset: Black-level offset setting used for the exposure.
        e_per_adu: Detector gain in e-/ADU.
        temperature: Sensor temperature in degC.
        base_temperature: Temperature of the base plate in degC.
        cooler_power: Cooler power in percent.
        setpoint: Cooler setpoint in degC.
        data: Pixel data, for DATAMIN, DATAMAX and DATAMEAN.
    """

    date_obs: datetime | str | None = None
    exposure_time: float | None = None
    instrument: str | None = None
    binning: tuple[int, int] | None = None
    window: tuple[int, int, int, int] | None = None
    pixel_size: float | None = None
    gain: float | None = None
    offset: float | None = None
    e_per_adu: float | None = None
    temperature: float | None = None
    base_temperature: float | None = None
    cooler_power: float | None = None
    setpoint: float | None = None
    data: NDArray[Any] | None = None


def make_frame_header(settings: FrameSettings) -> fits.Header:
    """Builds the header cards for a frame.

    Args:
        settings: What is known about the frame.

    Returns:
        A new header. Add it to an image with ``image.header.update(...)``, which keeps the comments.
    """
    s = settings
    hdr = fits.Header()

    if s.date_obs is not None:
        date_obs = s.date_obs if isinstance(s.date_obs, str) else s.date_obs.strftime("%Y-%m-%dT%H:%M:%S.%f")
        hdr["DATE-OBS"] = (date_obs, "Date and time of start of exposure")
    if s.exposure_time is not None:
        hdr["EXPTIME"] = (s.exposure_time, "Exposure time [s]")
    if s.instrument is not None:
        hdr["INSTRUME"] = (s.instrument, "Name of instrument")

    if s.binning is not None:
        hdr["XBINNING"] = hdr["DET-BIN1"] = (int(s.binning[0]), "Binning factor used on X axis")
        hdr["YBINNING"] = hdr["DET-BIN2"] = (int(s.binning[1]), "Binning factor used on Y axis")
    if s.window is not None:
        hdr["XORGSUBF"] = (int(s.window[0]), "Subframe origin on X axis")
        hdr["YORGSUBF"] = (int(s.window[1]), "Subframe origin on Y axis")

    if s.pixel_size is not None:
        hdr["DET-PIXL"] = (s.pixel_size, "Size of detector pixels (square) [mm]")
    if s.gain is not None:
        hdr["GAIN"] = (s.gain, "Gain used for exposure")
    if s.e_per_adu is not None:
        hdr["DET-GAIN"] = (s.e_per_adu, "Detector gain [e-/ADU]")
    if s.offset is not None:
        hdr["OFFSET"] = (s.offset, "Black-level offset used for exposure")

    if s.temperature is not None:
        hdr["DET-TEMP"] = (s.temperature, "CCD temperature [C]")
    if s.base_temperature is not None:
        hdr["DET-TBAS"] = (s.base_temperature, "Base plate temperature [C]")
    if s.cooler_power is not None:
        hdr["DET-COOL"] = (s.cooler_power, "Cooler power [percent]")
    if s.setpoint is not None:
        hdr["DET-TSET"] = (s.setpoint, "Cooler setpoint [C]")

    if s.data is not None:
        hdr["DATAMIN"] = (float(np.min(s.data)), "Minimum data value")
        hdr["DATAMAX"] = (float(np.max(s.data)), "Maximum data value")
        hdr["DATAMEAN"] = (float(np.mean(s.data)), "Mean data value")

    return hdr


__all__ = ["FrameSettings", "make_frame_header"]
