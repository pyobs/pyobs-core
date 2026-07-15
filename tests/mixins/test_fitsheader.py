from __future__ import annotations

import asyncio
from datetime import date
from unittest.mock import AsyncMock, MagicMock

import numpy as np
import pytest
from astropy.coordinates import EarthLocation

from pyobs.comm import Comm
from pyobs.images import Image
from pyobs.interfaces import FitsHeaderEntry, IFitsHeaderAfter, IFitsHeaderBefore
from pyobs.mixins.fitsheader import ImageFitsHeaderMixin
from pyobs.modules import Module
from pyobs.utils import exceptions as exc
from tests.helpers import make_proxy_cm


class FitsModule(Module, ImageFitsHeaderMixin):
    """Minimal concrete module for exercising ImageFitsHeaderMixin in isolation."""

    def __init__(self, **kwargs) -> None:
        Module.__init__(self, **kwargs)
        ImageFitsHeaderMixin.__init__(self, **kwargs)


DEFAULT_LOCATION = EarthLocation.from_geodetic(lon=20.81, lat=-32.38, height=1798.0)


def make_observer(
    lst_hours: float = 5.5, night: date = date(2024, 1, 1), location: EarthLocation = DEFAULT_LOCATION
) -> MagicMock:
    observer = MagicMock()
    observer.location = location
    lst = MagicMock()
    lst.hour = lst_hours
    observer.local_sidereal_time = MagicMock(return_value=lst)
    sunset = MagicMock()
    sunset.to_datetime = MagicMock(return_value=MagicMock(date=MagicMock(return_value=night)))
    observer.sun_set_time = MagicMock(return_value=sunset)
    return observer


def make_module(location: EarthLocation | None = ..., observer: MagicMock | None = ..., **kwargs) -> FitsModule:
    comm = MagicMock(spec=Comm)
    if location is ...:
        location = DEFAULT_LOCATION
    if observer is ...:
        observer = make_observer(location=location) if location is not None else None
    return FitsModule(comm=comm, location=location, observer=observer, **kwargs)


def make_image(**header: object) -> Image:
    image = Image(data=np.zeros((4, 4)))
    for key, value in header.items():
        image.header[key] = value
    return image


# ── __init__ ────────────────────────────────────────────────────────────────


def test_init_defaults() -> None:
    m = make_module()
    assert m._fitsheadermixin_filename_pattern == "/cache/pyobs-{DAY-OBS|date:}-{FRAMENUM|string:04d}.fits"
    assert m._fitsheadermixin_fits_headers["OBSERVER"] == ["pyobs", "Name of observer"]
    assert m._fitsheadermixin_night_obs is True
    assert m._fitsheadermixin_enable_frame_number is True
    assert m._fitsheadermixin_frame_number == 0


def test_init_preserves_custom_observer_header() -> None:
    m = make_module(fits_headers={"OBSERVER": ["custom", "who took it"]})
    assert m._fitsheadermixin_fits_headers["OBSERVER"] == ["custom", "who took it"]


def test_init_cache_path_uses_module_name() -> None:
    m = make_module()
    assert m._fitsheadermixin_cache == f"/pyobs/modules/{m.name}/cache.yaml"


# ── request_fits_headers ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_request_fits_headers_returns_empty_without_comm() -> None:
    m = make_module()
    m._comm = None

    futures = await m.request_fits_headers()

    assert futures == {}


@pytest.mark.asyncio
async def test_request_fits_headers_before_requests_from_clients() -> None:
    m = make_module()
    m._comm.clients_with_interface = AsyncMock(return_value=["camera1"])
    remote = MagicMock()
    remote.get_fits_header_before = AsyncMock(return_value={"X": FitsHeaderEntry(1, "c")})
    m._comm.proxy = MagicMock(return_value=make_proxy_cm(remote))

    futures = await m.request_fits_headers(before=True)

    m._comm.clients_with_interface.assert_awaited_once_with(IFitsHeaderBefore)
    assert "camera1" in futures
    result = await futures["camera1"]
    assert result == {"X": FitsHeaderEntry(1, "c")}


@pytest.mark.asyncio
async def test_request_fits_headers_after_requests_from_clients() -> None:
    m = make_module()
    m._comm.clients_with_interface = AsyncMock(return_value=["camera1"])
    remote = MagicMock()
    remote.get_fits_header_after = AsyncMock(return_value={})
    m._comm.proxy = MagicMock(return_value=make_proxy_cm(remote))

    futures = await m.request_fits_headers(before=False)

    m._comm.clients_with_interface.assert_awaited_once_with(IFitsHeaderAfter)
    assert "camera1" in futures


# ── add_requested_fits_headers ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_add_requested_fits_headers_adds_values() -> None:
    m = make_module()
    image = make_image()

    async def fut() -> dict:
        return {"FOO": FitsHeaderEntry(42, "the answer")}

    await m.add_requested_fits_headers(image, {"client1": asyncio.ensure_future(fut())})

    assert image.header["FOO"] == 42
    assert image.header.comments["FOO"] == "the answer"


@pytest.mark.asyncio
async def test_add_requested_fits_headers_skips_remote_error() -> None:
    m = make_module()
    image = make_image()

    async def fut() -> dict:
        raise exc.RemoteError("boom")

    # should not raise
    await m.add_requested_fits_headers(image, {"client1": asyncio.ensure_future(fut())})
    assert "FOO" not in image.header


@pytest.mark.asyncio
async def test_add_requested_fits_headers_skips_empty_headers() -> None:
    m = make_module()
    image = make_image()

    async def fut() -> dict:
        return {}

    header_keys_before = set(image.header.keys())
    await m.add_requested_fits_headers(image, {"client1": asyncio.ensure_future(fut())})
    # nothing added, no error
    assert set(image.header.keys()) == header_keys_before


# ── add_fits_headers (top-level orchestration) ──────────────────────────────


@pytest.mark.asyncio
async def test_add_fits_headers_sets_extname_and_static_headers() -> None:
    m = make_module(fits_headers={"FOO": ["bar", "a comment"]}, frame_number=False)
    image = make_image(**{"DATE-OBS": "2024-01-01T03:00:00.000"})

    await m.add_fits_headers(image)

    assert image.header["EXTNAME"] == "SCI"
    assert image.header["FOO"] == "bar"
    assert image.header["OBSERVER"] == "pyobs"


@pytest.mark.asyncio
async def test_add_fits_headers_adds_frame_number_when_enabled() -> None:
    m = make_module(frame_number=True)
    image = make_image(**{"DATE-OBS": "2024-01-01T03:00:00.000"})

    await m.add_fits_headers(image)

    assert image.header["FRAMENUM"] == 1


@pytest.mark.asyncio
async def test_add_fits_headers_skips_frame_number_when_disabled() -> None:
    m = make_module(frame_number=False)
    image = make_image(**{"DATE-OBS": "2024-01-01T03:00:00.000"})

    await m.add_fits_headers(image)

    assert "FRAMENUM" not in image.header


# ── _fitsheadermixin_add_fits_headers (base) ────────────────────────────────


def test_add_fits_headers_warns_and_skips_without_date_obs() -> None:
    # date-dependent headers are skipped entirely without DATE-OBS; the WCS projection
    # type (CTYPE1/2, set by the ImageFitsHeaderMixin override) is date-independent and
    # still gets added regardless
    m = make_module()
    image = make_image()

    m._fitsheadermixin_add_fits_headers(image)

    for key in ("MJD-OBS", "EQUINOX", "DAY-OBS", "LONGITUD", "LATITUDE", "HEIGHT", "LST"):
        assert key not in image.header


def test_add_fits_headers_sets_mjd_and_equinox() -> None:
    m = make_module()
    image = make_image(**{"DATE-OBS": "2024-01-01T03:00:00.000"})

    m._fitsheadermixin_add_fits_headers(image)

    assert image.header["EQUINOX"] == 2000.0
    assert image.header["MJD-OBS"] == pytest.approx(60310.125)


def test_add_fits_headers_sets_location_headers() -> None:
    m = make_module()
    image = make_image(**{"DATE-OBS": "2024-01-01T03:00:00.000"})

    m._fitsheadermixin_add_fits_headers(image)

    assert image.header["LONGITUD"] == pytest.approx(20.81)
    assert image.header["LATITUDE"] == pytest.approx(-32.38)
    assert image.header["HEIGHT"] == pytest.approx(1798.0)


def test_add_fits_headers_skips_location_headers_without_location() -> None:
    m = make_module(location=None, observer=None)
    image = make_image(**{"DATE-OBS": "2024-01-01T03:00:00.000"})

    m._fitsheadermixin_add_fits_headers(image)

    assert "LONGITUD" not in image.header
    # night_obs defaults to True, but with no observer to compute sunset from, falls
    # back to the plain calendar day instead of crashing
    assert image.header["DAY-OBS"] == "2024-01-01"


def test_add_fits_headers_sets_lst_when_observer_present() -> None:
    m = make_module(observer=make_observer(lst_hours=5.5))
    image = make_image(**{"DATE-OBS": "2024-01-01T03:00:00.000"})

    m._fitsheadermixin_add_fits_headers(image)

    assert image.header["LST"] == "05:30:00.00"


def test_add_fits_headers_sets_day_obs_from_night_obs() -> None:
    m = make_module(night_obs=True, observer=make_observer(night=date(2023, 12, 31)))
    image = make_image(**{"DATE-OBS": "2024-01-01T03:00:00.000"})

    m._fitsheadermixin_add_fits_headers(image)

    assert image.header["DAY-OBS"] == "2023-12-31"


def test_add_fits_headers_sets_day_obs_as_calendar_day_when_night_obs_disabled() -> None:
    m = make_module(night_obs=False)
    image = make_image(**{"DATE-OBS": "2024-01-01T03:00:00.000"})

    m._fitsheadermixin_add_fits_headers(image)

    assert image.header["DAY-OBS"] == "2024-01-01"


# ── _fitsheadermixin_add_framenum ───────────────────────────────────────────


@pytest.mark.asyncio
async def test_add_framenum_skips_gracefully_without_day_obs() -> None:
    m = make_module()
    image = make_image()

    # should not raise
    await m._fitsheadermixin_add_framenum(image)

    assert "FRAMENUM" not in image.header


@pytest.mark.asyncio
async def test_add_framenum_increments_and_sets_header() -> None:
    m = make_module()
    m._vfs = MagicMock()
    m._vfs.read_yaml = AsyncMock(side_effect=FileNotFoundError())
    m._vfs.write_yaml = AsyncMock()
    image = make_image(**{"DAY-OBS": "2024-01-01"})

    await m._fitsheadermixin_add_framenum(image)

    assert image.header["FRAMENUM"] == 1
    assert m._fitsheadermixin_frame_number == 1


@pytest.mark.asyncio
async def test_add_framenum_uses_cache_value_for_same_night() -> None:
    m = make_module()
    m._vfs = MagicMock()
    m._vfs.read_yaml = AsyncMock(return_value={"night": "2024-01-01", "framenum": 7})
    m._vfs.write_yaml = AsyncMock()
    image = make_image(**{"DAY-OBS": "2024-01-01"})

    await m._fitsheadermixin_add_framenum(image)

    assert image.header["FRAMENUM"] == 8
    m._vfs.write_yaml.assert_awaited_once_with(m._fitsheadermixin_cache, {"night": "2024-01-01", "framenum": 8})


@pytest.mark.asyncio
async def test_add_framenum_resets_on_new_night() -> None:
    m = make_module()
    m._vfs = MagicMock()
    m._vfs.read_yaml = AsyncMock(return_value={"night": "2023-12-31", "framenum": 99})
    m._vfs.write_yaml = AsyncMock()
    image = make_image(**{"DAY-OBS": "2024-01-01"})

    await m._fitsheadermixin_add_framenum(image)

    assert image.header["FRAMENUM"] == 1


@pytest.mark.asyncio
async def test_add_framenum_handles_missing_cache_gracefully() -> None:
    m = make_module()
    m._vfs = MagicMock()
    m._vfs.read_yaml = AsyncMock(side_effect=ValueError("bad yaml"))
    m._vfs.write_yaml = AsyncMock()
    image = make_image(**{"DAY-OBS": "2024-01-01"})

    # should not raise
    await m._fitsheadermixin_add_framenum(image)

    assert image.header["FRAMENUM"] == 1


@pytest.mark.asyncio
async def test_add_framenum_warns_when_write_fails() -> None:
    m = make_module()
    m._vfs = MagicMock()
    m._vfs.read_yaml = AsyncMock(side_effect=FileNotFoundError())
    m._vfs.write_yaml = AsyncMock(side_effect=FileNotFoundError())
    image = make_image(**{"DAY-OBS": "2024-01-01"})

    # should not raise despite write failure
    await m._fitsheadermixin_add_framenum(image)

    assert image.header["FRAMENUM"] == 1


# ── format_filename ──────────────────────────────────────────────────────────


def test_format_filename_returns_none_without_pattern() -> None:
    m = make_module()
    m._fitsheadermixin_filename_pattern = None
    image = make_image()

    assert m.format_filename(image) is None


def test_format_filename_formats_and_sets_headers() -> None:
    m = make_module(filenames="/webcam/pyobs-{DAY-OBS|date:}-{FRAMENUM|string:04d}.fits")
    image = make_image(**{"DAY-OBS": "2024-01-01", "FRAMENUM": 3})

    filename = m.format_filename(image)

    assert filename == "/webcam/pyobs-20240101-0003.fits"
    assert image.header["FNAME"] == "pyobs-20240101-0003.fits"
    assert image.header["ORIGNAME"] == "pyobs-20240101-0003.fits"


# ── rotation / centre properties ────────────────────────────────────────────


def test_rotation_and_centre_properties() -> None:
    m = make_module(centre=(512.0, 384.0), rotation=90.0)
    assert m.centre == (512.0, 384.0)
    assert m.rotation == 90.0


# ── ImageFitsHeaderMixin: WCS-related headers ───────────────────────────────


def test_sets_crval_from_radec() -> None:
    m = make_module()
    image = make_image(**{"DATE-OBS": "2024-01-01T03:00:00.000", "TEL-RA": 123.0, "TEL-DEC": -45.0})

    m._fitsheadermixin_add_fits_headers(image)

    assert image.header["CRVAL1"] == 123.0
    assert image.header["CRVAL2"] == -45.0


def test_calculates_cdelt_from_pixel_scale() -> None:
    m = make_module()
    image = make_image(
        **{
            "DATE-OBS": "2024-01-01T03:00:00.000",
            "DET-PIXL": 0.015,
            "TEL-FOCL": 8400.0,
            "DET-BIN1": 1,
            "DET-BIN2": 1,
        }
    )

    m._fitsheadermixin_add_fits_headers(image)

    assert "CDELT1" in image.header
    assert "CDELT2" in image.header
    assert image.header["CUNIT1"] == "deg"
    assert image.header["WCSAXES"] == 2
    assert image.header["CDELT1"] < 0  # x-axis increment is negative by convention
    assert image.header["CDELT2"] > 0


def test_calculates_cdelt_applies_focal_reduction() -> None:
    m = make_module()
    base = make_image(
        **{
            "DATE-OBS": "2024-01-01T03:00:00.000",
            "DET-PIXL": 0.015,
            "TEL-FOCL": 8400.0,
            "DET-BIN1": 1,
            "DET-BIN2": 1,
        }
    )
    m._fitsheadermixin_add_fits_headers(base)

    reduced = make_image(
        **{
            "DATE-OBS": "2024-01-01T03:00:00.000",
            "DET-PIXL": 0.015,
            "TEL-FOCL": 8400.0,
            "DET-BIN1": 1,
            "DET-BIN2": 1,
            "FOCL-RED": 2.0,
        }
    )
    m._fitsheadermixin_add_fits_headers(reduced)

    # FOCL-RED divides the plate scale, so the "reduced" image has a coarser (smaller) CDELT
    assert abs(reduced.header["CDELT1"]) == pytest.approx(abs(base.header["CDELT1"]) / 2.0)


def test_warns_when_pixel_scale_inputs_missing(caplog) -> None:
    import logging

    m = make_module()
    image = make_image(**{"DATE-OBS": "2024-01-01T03:00:00.000"})

    with caplog.at_level(logging.WARNING):
        m._fitsheadermixin_add_fits_headers(image)

    assert "CDELT1/CDELT2" in caplog.text
    assert "CDELT1" not in image.header


def test_sets_centre_pixel_when_configured() -> None:
    m = make_module(centre=(512.0, 384.0))
    image = make_image(**{"DATE-OBS": "2024-01-01T03:00:00.000"})

    m._fitsheadermixin_add_fits_headers(image)

    assert image.header["DET-CPX1"] == 512.0
    assert image.header["DET-CPX2"] == 384.0


def test_warns_when_centre_not_configured(caplog) -> None:
    import logging

    m = make_module()
    image = make_image(**{"DATE-OBS": "2024-01-01T03:00:00.000"})

    with caplog.at_level(logging.WARNING):
        m._fitsheadermixin_add_fits_headers(image)

    assert "DET-CPX1/DET-CPX2" in caplog.text


def test_calculates_crpix_with_offset() -> None:
    m = make_module(centre=(512.0, 384.0))
    image = make_image(
        **{
            "DATE-OBS": "2024-01-01T03:00:00.000",
            "DET-BIN1": 2,
            "DET-BIN2": 2,
            "XORGSUBF": 10,
            "YORGSUBF": 20,
        }
    )

    m._fitsheadermixin_add_fits_headers(image)

    assert image.header["CRPIX1"] == pytest.approx((512.0 - 10) / 2)
    assert image.header["CRPIX2"] == pytest.approx((384.0 - 20) / 2)


def test_calculates_crpix_without_offset_when_not_given() -> None:
    m = make_module(centre=(512.0, 384.0))
    image = make_image(**{"DATE-OBS": "2024-01-01T03:00:00.000", "DET-BIN1": 1, "DET-BIN2": 1})

    m._fitsheadermixin_add_fits_headers(image)

    assert image.header["CRPIX1"] == 512.0
    assert image.header["CRPIX2"] == 384.0


def test_skips_wcs_projection_for_dark_and_bias() -> None:
    m = make_module(rotation=90.0)
    image = make_image(**{"DATE-OBS": "2024-01-01T03:00:00.000", "IMAGETYP": "dark"})

    m._fitsheadermixin_add_fits_headers(image)

    assert "CTYPE1" not in image.header
    assert "PC1_1" not in image.header


def test_sets_ctype_and_pc_matrix_for_object_images() -> None:
    m = make_module(rotation=90.0)
    image = make_image(**{"DATE-OBS": "2024-01-01T03:00:00.000", "IMAGETYP": "object"})

    m._fitsheadermixin_add_fits_headers(image)

    assert image.header["CTYPE1"] == "RA---TAN"
    assert image.header["CTYPE2"] == "DEC--TAN"
    assert image.header["POSANG"] == pytest.approx(90.0)
    assert image.header["PC1_1"] == pytest.approx(0.0, abs=1e-9)
    assert image.header["PC2_1"] == pytest.approx(1.0, abs=1e-9)


def test_does_not_override_existing_ctype() -> None:
    m = make_module(rotation=90.0)
    image = make_image(**{"DATE-OBS": "2024-01-01T03:00:00.000", "CTYPE1": "CUSTOM"})

    m._fitsheadermixin_add_fits_headers(image)

    assert image.header["CTYPE1"] == "CUSTOM"


def test_posang_includes_derotoff() -> None:
    m = make_module(rotation=10.0)
    image = make_image(**{"DATE-OBS": "2024-01-01T03:00:00.000", "DEROTOFF": 5.0})

    m._fitsheadermixin_add_fits_headers(image)

    assert image.header["POSANG"] == pytest.approx(15.0)


def test_warns_without_rotation(caplog) -> None:
    import logging

    m = make_module(rotation=None)
    image = make_image(**{"DATE-OBS": "2024-01-01T03:00:00.000"})

    with caplog.at_level(logging.WARNING):
        m._fitsheadermixin_add_fits_headers(image)

    assert "CD matrix" in caplog.text
    assert "PC1_1" not in image.header
