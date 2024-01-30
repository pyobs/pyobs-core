from unittest.mock import Mock

import numpy as np
import pytest
import scipy.optimize

from pyobs.images.processors.offsets._gaussian_fitter import GaussianFitter


@pytest.fixture()
def gaussian_data():
    return np.array([
        [
            GaussianFitter._gauss2d([x, y], 1, 2, 10, 10, 1, 1) for x in range(21)
        ] for y in range(21)
    ])


def test_offsets_from_corr(gaussian_data) -> None:
    result = GaussianFitter().offsets_from_corr(gaussian_data.astype(float))

    np.testing.assert_array_almost_equal(result, (0.0, 0.0), 10)


def test_offsets_from_corr_err(gaussian_data) -> None:
    scipy.optimize.curve_fit = Mock(side_effect=RuntimeError)

    result = GaussianFitter().offsets_from_corr(gaussian_data.astype(float))
    assert result == (0.0, 0.0)


def test_check_corr_border() -> None:
    corr = np.zeros((10, 10))

    with pytest.raises(Exception):
        GaussianFitter._check_peak_border_distance(corr.astype(float), 4, 4)


def test_check_fit_quality() -> None:
    xdata_restricted = np.array([[0.0], [0.0]])
    ydata_restricted = np.array([[0.0], [0.0]])
    popt = (0.0, 1.0, 0.0, 0.0, 1.0, 1.0)

    with pytest.raises(Exception):
        GaussianFitter._check_fit_quality(xdata_restricted, ydata_restricted, popt)
