import logging

import numpy as np
import pytest
from astropy.table import Table

import pyobs.utils.pipeline
from pyobs.images import Image
from pyobs.images.processors.calibration import Calibration
from pyobs.images.processors.calibration._ccddata_calibrator import _CCDDataCalibrator
from pyobs.robotic.utils.archive import Archive
from pyobs.utils.enums import ImageType


class ConcreteArchive(Archive):
    """Minimal concrete Archive for testing."""

    async def list_options(self, **kwargs):
        return {}

    async def list_frames(self, **kwargs):
        return []

    async def download_frames(self, frames):
        return []


@pytest.fixture()
def mock_image():
    image = Image()
    image.header["INSTRUME"] = "cam"
    image.header["XBINNING"] = 1
    image.header["FILTER"] = "filter"
    image.header["DATE-OBS"] = "2023-11-20 07:53:29.653"
    image.header["EXPTIME"] = 30.0

    return image


@pytest.mark.asyncio
async def test_find_master_in_cache(mocker, mock_image):
    cached_image = Image()
    image_type = ImageType.OBJECT

    archive = ConcreteArchive()
    calibration = Calibration(archive)
    assert calibration._calib_cache is not None
    mocker.patch.object(calibration._calib_cache, "get_from_cache", return_value=cached_image)
    result_image = await calibration._find_master(mock_image, image_type)

    assert cached_image == result_image


@pytest.mark.asyncio
async def test_find_master_not_in_archive(mocker, mock_image):
    mocker.patch("pyobs.utils.pipeline.Pipeline.find_master", return_value=None)

    image_type = ImageType.OBJECT
    archive = ConcreteArchive()

    calibration = Calibration(archive)
    assert calibration._calib_cache is not None
    mocker.patch.object(calibration._calib_cache, "get_from_cache", side_effect=ValueError())

    with pytest.raises(ValueError):
        await calibration._find_master(mock_image, image_type)

    call = pyobs.utils.pipeline.Pipeline.find_master.call_args_list[0]
    assert call.args[0] == archive
    assert call.args[1] == image_type
    assert call.args[2].to_string() == "2023-11-20 07:53:29.653"
    assert call.args[3] == mock_image.header["INSTRUME"]
    assert call.args[4] == "1x1"
    assert call.args[5] == mock_image.header["FILTER"]
    assert call.kwargs["max_days"] is None


@pytest.mark.asyncio
async def test_find_master_in_archive(mocker, mock_image):
    calib_image = Image()

    mocker.patch("pyobs.utils.pipeline.Pipeline.find_master", return_value=calib_image)

    image_type = ImageType.OBJECT
    archive = ConcreteArchive()
    calibration = Calibration(archive)
    assert calibration._calib_cache is not None
    mocker.patch.object(calibration._calib_cache, "add_to_cache")

    assert calib_image == await calibration._find_master(mock_image, image_type)
    calibration._calib_cache.add_to_cache.assert_called_once_with(calib_image, image_type)


@pytest.mark.asyncio
async def test_call_valid(mocker, mock_image):
    mock_image.header["DET-GAIN"] = 1.0
    mock_image.header["DET-RON"] = 0.0
    mock_image.header["EXPTIME"] = 1.0
    mock_image.header["ORIGNAME"] = "file.fits"
    mock_image.header["FNAME"] = "file.fits.fz"

    calib_image = Image()
    mocker.patch("ccdproc.ccd_process", return_value=calib_image)
    mocker.patch("pyobs.images.Image.from_ccddata", return_value=calib_image)
    mocker.patch("pyobs.images.Image.to_ccddata", return_value=calib_image)

    archive = ConcreteArchive()
    calibration = Calibration(archive)
    mocker.patch.object(calibration, "_find_master", return_value=mock_image)
    mocker.patch.object(calibration, "_find_dark_master", return_value=(mock_image, False))

    result_image = await calibration(mock_image)

    assert result_image.header["RLEVEL"] == 1
    assert result_image.header["BUNIT"] == "electron"

    assert result_image.header["L1RAW"] == "file"
    assert result_image.header["L1BIAS"] == "file"
    assert result_image.header["L1DARK"] == "file"
    assert result_image.header["L1FLAT"] == "file"

    assert calib_image == result_image


@pytest.mark.asyncio
async def test_call_calibration_not_found(mocker, caplog):
    archive = ConcreteArchive()
    calibration = Calibration(archive)

    mocker.patch.object(calibration, "_get_calibrations_masters", side_effect=ValueError("Test"))

    image = Image()
    with caplog.at_level(logging.WARNING):
        result_image = await calibration(image)

    assert caplog.records[0].message == "Could not find calibration frames: Test"
    assert image == result_image


def test_ccddata_calibrator_drops_preexisting_catalog_before_trim():
    # a catalog already attached to the raw science frame (e.g. quick-look photometry at the
    # telescope) must not block calibration, since to_ccddata() never carries it through anyway
    image = Image(data=np.zeros((4, 4), dtype=np.float32))
    image.catalog = Table({"x": [1.0]})

    calibrator = _CCDDataCalibrator(image)

    assert calibrator._image.safe_catalog is None
    assert image.safe_catalog is not None  # original image is untouched


def test_verify_image_header_invalid():
    image = Image()

    with pytest.raises(ValueError):
        Calibration._verify_image_header(image)


def test_verify_image_header_requires_exptime():
    image = Image()
    image.header["INSTRUME"] = "cam"
    image.header["XBINNING"] = 1
    image.header["DATE-OBS"] = "2023-11-20 07:53:29.653"

    with pytest.raises(ValueError):
        Calibration._verify_image_header(image)


def _dark_master(exptime: float) -> Image:
    # real dark masters inherit INSTRUME/XBINNING from the raw frames combined into them, and
    # the calibration cache derives its key from these on the master, not the science image
    master = Image()
    master.header["INSTRUME"] = "cam"
    master.header["XBINNING"] = 1
    master.header["EXPTIME"] = exptime
    return master


def _find_master_side_effect(exact: Image | None = None, reference: Image | None = None, fallback: Image | None = None):
    """Fakes Pipeline.find_master for _find_dark_master tests: _find_dark_at's exact-match call
    passes exptime= without exptime_max=, its reference call passes both, and the branch-4
    fallback (via _find_master -> _find_master_in_archive) passes neither."""

    def side_effect(*args, **kwargs):
        if kwargs.get("exptime_max") is not None:
            return reference
        if "exptime" in kwargs:
            return exact
        return fallback

    return side_effect


# ── _find_dark_master (ADR 0015 policy) ────────────────────────────────────────


@pytest.mark.asyncio
async def test_find_dark_master_require_dark_false_skips_lookup(mocker, mock_image):
    mocker.patch("pyobs.utils.pipeline.Pipeline.find_master")
    calibration = Calibration(ConcreteArchive(), require_dark=False)

    master, scale = await calibration._find_dark_master(mock_image)

    assert (master, scale) == (None, False)
    pyobs.utils.pipeline.Pipeline.find_master.assert_not_called()


@pytest.mark.asyncio
async def test_find_dark_master_exact_match_used_unscaled(mocker, mock_image):
    mock_image.header["EXPTIME"] = 600.0
    exact = _dark_master(600.0)
    mocker.patch("pyobs.utils.pipeline.Pipeline.find_master", side_effect=_find_master_side_effect(exact=exact))

    calibration = Calibration(ConcreteArchive())
    master, scale = await calibration._find_dark_master(mock_image)

    assert master is exact
    assert scale is False


@pytest.mark.asyncio
async def test_find_dark_master_legacy_master_with_no_exptime_is_not_an_exact_match(mocker, mock_image):
    # a legacy pre-#831 master with no EXPTIME header at all must fall through to the rest of
    # the policy (here: strict error) rather than raising a bare KeyError
    mock_image.header["EXPTIME"] = 600.0
    legacy = Image()
    legacy.header["INSTRUME"] = "cam"
    legacy.header["XBINNING"] = 1
    mocker.patch("pyobs.utils.pipeline.Pipeline.find_master", side_effect=_find_master_side_effect(exact=legacy))

    calibration = Calibration(ConcreteArchive())
    with pytest.raises(ValueError, match="EXPTIME=600.0"):
        await calibration._find_dark_master(mock_image)


@pytest.mark.asyncio
async def test_find_dark_master_below_minimum_is_bias_only(mocker, mock_image):
    mock_image.header["EXPTIME"] = 2.0  # below the default dark_min_exptime=5.0
    mocker.patch("pyobs.utils.pipeline.Pipeline.find_master", side_effect=_find_master_side_effect())

    calibration = Calibration(ConcreteArchive())
    master, scale = await calibration._find_dark_master(mock_image)

    assert (master, scale) == (None, False)


@pytest.mark.asyncio
async def test_find_dark_master_exact_match_below_minimum_wins_over_bias_only(mocker, mock_image):
    mock_image.header["EXPTIME"] = 2.0
    exact = _dark_master(2.0)
    mocker.patch("pyobs.utils.pipeline.Pipeline.find_master", side_effect=_find_master_side_effect(exact=exact))

    calibration = Calibration(ConcreteArchive())
    master, scale = await calibration._find_dark_master(mock_image)

    assert master is exact
    assert scale is False


@pytest.mark.asyncio
async def test_find_dark_master_reference_scaled_down(mocker, mock_image):
    mock_image.header["EXPTIME"] = 45.0
    reference = _dark_master(600.0)
    mocker.patch("pyobs.utils.pipeline.Pipeline.find_master", side_effect=_find_master_side_effect(reference=reference))

    calibration = Calibration(ConcreteArchive())
    master, scale = await calibration._find_dark_master(mock_image)

    assert master is reference
    assert scale is True


@pytest.mark.asyncio
async def test_find_dark_master_science_exptime_above_reference_skips_scale_branch(mocker, mock_image):
    # EXPTIME > dark_scale_exptime -- branch 3 must not fire even if a reference exists,
    # otherwise the reference would be scaled UP, which ADR 0015 forbids
    mock_image.header["EXPTIME"] = 900.0
    reference = _dark_master(600.0)
    mocker.patch("pyobs.utils.pipeline.Pipeline.find_master", side_effect=_find_master_side_effect(reference=reference))

    calibration = Calibration(ConcreteArchive())
    with pytest.raises(ValueError):
        await calibration._find_dark_master(mock_image)


@pytest.mark.asyncio
async def test_find_dark_master_allow_unmatched_dark_scale_falls_back(mocker, mock_image):
    mock_image.header["EXPTIME"] = 45.0
    fallback = _dark_master(123.0)
    mocker.patch("pyobs.utils.pipeline.Pipeline.find_master", side_effect=_find_master_side_effect(fallback=fallback))

    calibration = Calibration(ConcreteArchive(), dark_scale_exptime=None, allow_unmatched_dark_scale=True)
    master, scale = await calibration._find_dark_master(mock_image)

    assert master is fallback
    assert scale is True


@pytest.mark.asyncio
async def test_find_dark_master_strict_no_match_raises(mocker, mock_image):
    mock_image.header["EXPTIME"] = 45.0
    mocker.patch("pyobs.utils.pipeline.Pipeline.find_master", side_effect=_find_master_side_effect())

    calibration = Calibration(ConcreteArchive())
    with pytest.raises(ValueError, match="EXPTIME=45.0"):
        await calibration._find_dark_master(mock_image)


@pytest.mark.asyncio
async def test_find_dark_master_dark_min_exptime_none_disables_bias_only_branch(mocker, mock_image):
    mock_image.header["EXPTIME"] = 2.0
    reference = _dark_master(600.0)
    mocker.patch("pyobs.utils.pipeline.Pipeline.find_master", side_effect=_find_master_side_effect(reference=reference))

    calibration = Calibration(ConcreteArchive(), dark_min_exptime=None)
    master, scale = await calibration._find_dark_master(mock_image)

    # no exact match, and dark_min_exptime disabled -- falls through to the reference branch
    # instead of returning the bias-only (None, False)
    assert master is reference
    assert scale is True


# ── _CCDDataCalibrator dark_scale ──────────────────────────────────────────────


def test_ccddata_calibrator_unscaled_dark_passes_no_dark_exposure(mocker):
    image = Image(data=np.zeros((2, 2), dtype=np.float32))
    image.header["DET-GAIN"] = 1.0
    image.header["DET-RON"] = 0.0
    image.header["EXPTIME"] = 600.0

    dark = Image(data=np.zeros((2, 2), dtype=np.float32))
    dark.header["EXPTIME"] = 600.0

    mock_ccd_process = mocker.patch("ccdproc.ccd_process")
    calibrator = _CCDDataCalibrator(image, dark=dark, dark_scale=False)
    calibrator()

    assert mock_ccd_process.call_args.kwargs["dark_scale"] is False
    assert mock_ccd_process.call_args.kwargs["dark_exposure"] is None


def test_ccddata_calibrator_scaled_dark_passes_dark_exposure(mocker):
    image = Image(data=np.zeros((2, 2), dtype=np.float32))
    image.header["DET-GAIN"] = 1.0
    image.header["DET-RON"] = 0.0
    image.header["EXPTIME"] = 45.0

    dark = Image(data=np.zeros((2, 2), dtype=np.float32))
    dark.header["EXPTIME"] = 600.0

    mock_ccd_process = mocker.patch("ccdproc.ccd_process")
    calibrator = _CCDDataCalibrator(image, dark=dark, dark_scale=True)
    calibrator()

    assert mock_ccd_process.call_args.kwargs["dark_scale"] is True
    assert mock_ccd_process.call_args.kwargs["dark_exposure"] is not None
