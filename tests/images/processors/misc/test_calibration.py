import logging
import pytest

import pyobs.utils.pipeline
from pyobs.images import Image
from pyobs.images.processors.calibration import Calibration
from pyobs.utils.archive import Archive
from pyobs.utils.enums import ImageType


@pytest.fixture()
def mock_image():
    image = Image()
    image.header["INSTRUME"] = "cam"
    image.header["XBINNING"] = 1
    image.header["FILTER"] = "filter"
    image.header["DATE-OBS"] = "2023-11-20 07:53:29.653"

    return image


@pytest.mark.asyncio
async def test_find_master_in_cache(mocker, mock_image):
    cached_image = Image()
    image_type = ImageType.OBJECT

    archive = Archive()
    calibration = Calibration(archive)
    assert calibration._calib_cache is not None
    mocker.patch.object(calibration._calib_cache, "get_from_cache", return_value=cached_image)
    result_image = await calibration._find_master(mock_image, image_type)

    assert cached_image == result_image


@pytest.mark.asyncio
async def test_find_master_not_in_archive(mocker, mock_image):
    mocker.patch("pyobs.utils.pipeline.Pipeline.find_master", return_value=None)

    image_type = ImageType.OBJECT
    archive = Archive()

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
    archive = Archive()
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
    mocker.patch("pyobs.utils.pipeline.Pipeline.trim_ccddata", return_value=mock_image)
    mocker.patch("ccdproc.ccd_process", return_value=calib_image)
    mocker.patch("pyobs.images.Image.from_ccddata", return_value=calib_image)
    mocker.patch("pyobs.images.Image.to_ccddata", return_value=calib_image)

    archive = Archive()
    calibration = Calibration(archive)
    mocker.patch.object(calibration, "_find_master", return_value=mock_image)

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
    archive = Archive()
    calibration = Calibration(archive)

    mocker.patch.object(calibration, "_get_calibrations_masters", side_effect=ValueError("Test"))

    image = Image()
    with caplog.at_level(logging.WARNING):
        result_image = await calibration(image)

    assert caplog.records[0].message == "Could not find calibration frames: Test"
    assert image == result_image


def test_verify_image_header_invalid():
    image = Image()

    with pytest.raises(ValueError):
        Calibration._verify_image_header(image)
