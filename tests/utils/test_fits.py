from __future__ import annotations

from astropy.io import fits

from pyobs.utils.fits import FilenameFormatter


def test_format_exptime_renders_whole_seconds_without_trailing_zero() -> None:
    hdr = fits.Header({"EXPTIME": 600.0})
    formatter = FilenameFormatter("{EXPTIME|exptime}")

    assert formatter(hdr) == "600"


def test_format_exptime_keeps_fractional_seconds() -> None:
    hdr = fits.Header({"EXPTIME": 0.333})
    formatter = FilenameFormatter("{EXPTIME|exptime}")

    assert formatter(hdr) == "0.333"


def test_format_exptime_missing_key_renders_placeholder_instead_of_raising() -> None:
    # a legacy dark master combined from raw frames with no EXPTIME at all -- format_filename()
    # must still succeed so the master can be stored, not raise KeyError
    hdr = fits.Header({})
    formatter = FilenameFormatter("{EXPTIME|exptime}")

    assert formatter(hdr) == "unknown"
