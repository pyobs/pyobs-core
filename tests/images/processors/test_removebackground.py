import numpy as np
import photutils.background

from pyobs.images import Image
from pyobs.images.processors._daobackgroundremover import _DaoBackgroundRemover


def test_init():
    sigma = 1.0
    box_size = (10, 10)
    filter_size = (3, 3)
    remover = _DaoBackgroundRemover(sigma, box_size, filter_size)

    assert remover._sigma_clip.sigma == sigma
    assert remover._box_size == box_size
    assert remover._filter_size == filter_size


def test_estimate_background_background2d_call(mocker):
    sigma = 3.0
    box_size = (1, 1)
    filter_size = (3, 3)
    spy = mocker.spy(photutils.background.Background2D, "__init__")
    remover = _DaoBackgroundRemover(sigma, box_size, filter_size)

    data = np.ones((20, 20))
    mask = np.zeros((20, 20)).astype(bool)
    image = Image(data=data, mask=mask)
    remover._estimate_background(image)
    spy.assert_called_once()

    args = spy.call_args[0]
    np.testing.assert_array_equal(args[1], data)
    kwargs = spy.call_args.kwargs
    assert kwargs["box_size"] == box_size
    assert kwargs["filter_size"] == filter_size
    assert kwargs["sigma_clip"].sigma == sigma
    assert kwargs["bkg_estimator"] == remover._bkg_estimator
    np.testing.assert_array_equal(kwargs["mask"], mask)


def test_call_const_background(mocker):
    sigma = 3.0
    box_size = (1, 1)
    filter_size = (3, 3)

    remover = _DaoBackgroundRemover(sigma, box_size, filter_size)

    image = Image(data=np.ones((20, 20)))
    output_image = remover(image)

    np.testing.assert_array_equal(output_image.data, np.zeros((20, 20)))
