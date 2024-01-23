import numpy as np
import pytest

from pyobs.images.processors.offsets._gaussian_fitter import GaussianFitter


def test_offsets_from_corr() -> None:
    corr = np.array([
        [
           GaussianFitter._gauss2d([x, y], 1, 2, 10, 10, 1, 1) for x in range(21)
        ] for y in range(21)
    ])

    result = GaussianFitter().offsets_from_corr(corr.astype(float))

    np.testing.assert_array_almost_equal(result, (0.0, 0.0), 10)


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
