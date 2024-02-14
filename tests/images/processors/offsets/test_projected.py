import logging
from unittest.mock import Mock

import numpy as np
import pytest
from scipy.signal.windows import gaussian

from pyobs.images import Image
from pyobs.images.meta import PixelOffsets
from pyobs.images.processors.offsets import ProjectedOffsets


@pytest.mark.asyncio
async def test_reset(caplog):
    offsets = ProjectedOffsets()
    offsets._ref_image = np.zeros((2, 2))

    with caplog.at_level(logging.INFO):
        await offsets.reset()

    assert offsets._ref_image is None


def test_gaussian():
    np.testing.assert_array_equal(ProjectedOffsets._gaussian([2, 1, 1], np.array(1.0)), np.array(2.0))


def test_gaussian_fit(mocker):
    mocker.patch('pyobs.images.processors.offsets.ProjectedOffsets._gaussian', return_value=np.ones((4, 1)))
    gaussian_params = [2, 1, 1]

    err = ProjectedOffsets._gaussian_fit(gaussian_params, np.zeros((4, 1)), np.zeros((4, 1)))
    assert err == 4.0


def test_calc_1d_offset():
    signal = gaussian(20, 5.0, sym=True)
    ref_data = np.pad(signal, (5, 0), mode='constant', constant_values=0)
    img_data = np.pad(signal, (0, 5), mode='constant', constant_values=0)   # Pad behind signal, to match data length

    shift = ProjectedOffsets._calc_1d_offset(ref_data, img_data, fit_width=15)

    np.testing.assert_almost_equal(shift, 5.0, decimal=4)


def test_subtract_sky_constant():
    data = np.ones(30)

    subtracted_data = ProjectedOffsets._subtract_sky(data)
    np.testing.assert_array_almost_equal(subtracted_data, np.zeros(30), decimal=4)


def test_process_axis_collapse():
    offsets = ProjectedOffsets()
    ProjectedOffsets._subtract_sky = Mock(return_value=np.ones(10))

    image = Image(data=np.ones((10, 10)))
    result = offsets._process(image)

    np.testing.assert_array_equal(result[0], np.ones(10))
    np.testing.assert_array_equal(result[1], np.ones(10))

    np.testing.assert_array_equal(offsets._subtract_sky.call_args_list[0][0][0], np.ones(10) * 10)
    np.testing.assert_array_equal(offsets._subtract_sky.call_args_list[1][0][0], np.ones(10) * 10)


def test_process_invalid_timsec():
    offsets = ProjectedOffsets()

    image = Image(data=np.ones((10, 10)))
    image.header["TRIMSEC"] = "INVALID"

    with pytest.raises(ValueError):
        offsets._process(image)


def test_process_valid_timsec():
    offsets = ProjectedOffsets()
    ProjectedOffsets._subtract_sky = Mock(return_value=np.ones(10))

    image = Image(data=np.ones((10, 10)))
    image.header["TRIMSEC"] = "[2:9,2:9]"

    offsets._process(image)

    np.testing.assert_array_equal(offsets._subtract_sky.call_args_list[0][0][0], np.ones(8) * 8)
    np.testing.assert_array_equal(offsets._subtract_sky.call_args_list[1][0][0], np.ones(8) * 8)


@pytest.mark.asyncio
async def test_call_ref(mocker, caplog):
    offsets = ProjectedOffsets()
    mocker.patch.object(offsets, "_process", return_value=(np.ones(10)*10, np.ones(10)*10))
    image = Image(data=np.ones((10, 10)))

    with caplog.at_level(logging.INFO):
        assert await offsets(image) == image

    np.testing.assert_array_equal(offsets._ref_image[0], np.ones(10) * 10)
    np.testing.assert_array_equal(offsets._ref_image[1], np.ones(10) * 10)
    assert caplog.messages[0] == "Initialising auto-guiding with new image..."


@pytest.mark.asyncio
async def test_call_no_corr(mocker, caplog):
    offsets = ProjectedOffsets()
    offsets._ref_image = (np.ones(10) * 10, np.ones(10) * 10)
    mocker.patch.object(offsets, "_process", return_value=(np.ones(10) * 10, np.ones(10) * 10))
    mocker.patch.object(offsets, "_calc_1d_offset", return_value=None)
    image = Image(data=np.ones((10, 10)))

    with caplog.at_level(logging.INFO):
        assert await offsets(image) == image

    assert caplog.messages[0] == "Perform auto-guiding on new image..."
    assert caplog.messages[1] == "Could not correlate peaks."


@pytest.mark.asyncio
async def test_call(mocker):
    offsets = ProjectedOffsets()
    offsets._ref_image = (np.ones(10) * 10, np.ones(10) * 10)

    mocker.patch.object(offsets, "_process", return_value=(np.ones(10) * 10, np.ones(10) * 10))
    mocker.patch.object(offsets, "_calc_1d_offset", return_value=10)
    image = Image(data=np.ones((10, 10)))

    result = await offsets(image)

    assert result.get_meta(PixelOffsets).dx == 10
    assert result.get_meta(PixelOffsets).dy == 10
