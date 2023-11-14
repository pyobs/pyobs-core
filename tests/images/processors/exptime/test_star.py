import logging
from copy import copy

import numpy as np
import pytest
from astropy.table import QTable

from pyobs.images import Image
from pyobs.images.processors.exptime import StarExpTimeEstimator


@pytest.fixture()
def mock_table() -> QTable:
    table = QTable()
    table['peak'] = [2500, 2000, 40, 30]
    table['x'] = [30, 25, 80, 90]
    table['y'] = [10, 40, 25, 60]

    return table


@pytest.mark.asyncio
async def test_full_wout_satu_header(mock_table):
    mock_image = Image(catalog=mock_table)
    mock_image.header["NAXIS0"] = 100
    mock_image.header["NAXIS1"] = 100

    mock_image.header["EXPTIME"] = 1.0

    estimator = StarExpTimeEstimator(saturated=0.1, bias=0.0)

    exp_time = await estimator._calc_exp_time(mock_image)

    assert exp_time == 2.0


def test_calc_saturation_level_or_default():
    mock_image = Image()

    mock_image.header["DET-SATU"] = 48000.0
    mock_image.header["DET-GAIN"] = 2.0

    estimator = StarExpTimeEstimator(saturated=0.1, bias=0.0)
    estimator._image = mock_image

    assert estimator._calc_saturation_level_or_default() == 24000.0


def test_filter_edge_stars_axis(mock_table):
    mock_image = Image(np.zeros((100, 100)), catalog=copy(mock_table))
    mock_image.header["NAXIS0"] = 100
    mock_image.header["NAXIS1"] = 100

    estimator = StarExpTimeEstimator(saturated=0.1, bias=0.0, edge=0.2)
    estimator._image = mock_image
    estimator._filter_edge_stars_axis(0)

    result_table = estimator._image.catalog

    np.testing.assert_array_equal(result_table["peak"], mock_table[:-1]["peak"])
    np.testing.assert_array_equal(result_table["x"], mock_table[:-1]["x"])
    np.testing.assert_array_equal(result_table["y"], mock_table[:-1]["y"])


def test_log_brightest_star(caplog):
    star = {"peak": 10.0, "x": 40.0, "y": 30.0}

    with caplog.at_level(logging.INFO):
        StarExpTimeEstimator._log_brightest_star(star)

    assert caplog.records[-1].message == "Found peak of 10.00 at 40.0x30.0."
