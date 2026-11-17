from datetime import UTC, datetime

import numpy as np
from astropy.io import fits

from pyobs.utils.frameheader import FrameSettings, make_frame_header


def test_nothing_known_gives_an_empty_header() -> None:
    assert len(make_frame_header(FrameSettings())) == 0


def test_binning_goes_into_both_key_pairs() -> None:
    hdr = make_frame_header(FrameSettings(binning=(1, 1)))
    assert set(hdr.keys()) == {"XBINNING", "DET-BIN1", "YBINNING", "DET-BIN2"}


def test_full_settings() -> None:
    data = np.array([[1, 2], [3, 6]], dtype=np.uint16)
    hdr = make_frame_header(
        FrameSettings(
            date_obs=datetime(2026, 11, 17, 10, 0, 0, 500000, tzinfo=UTC),
            exposure_time=300.0,
            instrument="ZWO ASI2600MM Pro",
            binning=(2, 3),
            window=(10, 20, 100, 100),
            pixel_size=0.00376,
            gain=100,
            offset=50,
            e_per_adu=0.248,
            temperature=-9.8,
            base_temperature=21.0,
            cooler_power=12,
            setpoint=-10.0,
            data=data,
        )
    )
    assert hdr["DATE-OBS"] == "2026-11-17T10:00:00.500000"
    assert hdr["EXPTIME"] == 300.0 and hdr["INSTRUME"] == "ZWO ASI2600MM Pro"
    assert hdr["XBINNING"] == hdr["DET-BIN1"] == 2 and hdr["YBINNING"] == hdr["DET-BIN2"] == 3
    assert hdr["XORGSUBF"] == 10 and hdr["YORGSUBF"] == 20
    assert hdr["DET-PIXL"] == 0.00376
    assert hdr["GAIN"] == 100 and hdr["OFFSET"] == 50 and hdr["DET-GAIN"] == 0.248
    assert hdr["DET-TEMP"] == -9.8 and hdr["DET-TBAS"] == 21.0
    assert hdr["DET-COOL"] == 12 and hdr["DET-TSET"] == -10.0
    assert (hdr["DATAMIN"], hdr["DATAMAX"], hdr["DATAMEAN"]) == (1.0, 6.0, 3.0)


def test_date_obs_string_is_kept() -> None:
    assert make_frame_header(FrameSettings(date_obs="2026-01-01T00:00:00.000"))["DATE-OBS"] == "2026-01-01T00:00:00.000"


def test_none_fields_are_left_out() -> None:
    hdr = make_frame_header(FrameSettings(exposure_time=1.0))
    for key in (
        "DATE-OBS",
        "INSTRUME",
        "XBINNING",
        "XORGSUBF",
        "DET-PIXL",
        "GAIN",
        "OFFSET",
        "DET-TEMP",
        "DET-COOL",
        "DATAMIN",
    ):
        assert key not in hdr


def test_update_keeps_comments() -> None:
    target = fits.Header()
    target.update(make_frame_header(FrameSettings(exposure_time=1.0)))
    assert target.comments["EXPTIME"] == "Exposure time [s]"
