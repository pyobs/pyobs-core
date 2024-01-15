import numpy as np

from scipy.signal.windows import gaussian
from pyobs.images.processors.offsets import ProjectedOffsets


def test_gaussian():
    np.testing.assert_array_equal(ProjectedOffsets._gaussian([2, 1, 1], np.array(1.0)), np.array(2.0))


def test_gaussian_fit(mocker):
    mocker.patch('pyobs.images.processors.offsets.ProjectedOffsets._gaussian', return_value=np.ones((4, 1)))
    gaussian_params = [2, 1, 1]

    err = ProjectedOffsets._gaussian_fit(gaussian_params, np.zeros((4, 1)), np.zeros((4, 1)))
    assert err == 4.0


def test_correlate():
    signal = gaussian(20, 5.0, sym=True)
    ref_data = np.pad(signal, (5, 0), mode='constant', constant_values=0)
    img_data = np.pad(signal, (0, 5), mode='constant', constant_values=0)   # Pad behind signal, to match data length

    shift = ProjectedOffsets._correlate(ref_data, img_data, fit_width=15)

    np.testing.assert_almost_equal(shift, 5.0, decimal=4)


def test_subtract_sky_constant():
    data = np.ones(30)

    subtracted_data = ProjectedOffsets._subtract_sky(data)
    np.testing.assert_array_almost_equal(subtracted_data, np.zeros(30), decimal=4)
