import pytest

from pyobs.images.processors.exptime import ExpTimeEstimator
from pyobs.images import Image


class TestExpTimeEstimator(ExpTimeEstimator):
    async def _calc_exp_time(self, image: Image) -> float:
        pass


@pytest.mark.asyncio
async def test_call(mocker):
    estimator = TestExpTimeEstimator(5., 10.)
    image = Image()

    mocker.patch.object(estimator, "_calc_exp_time", return_value=1.0)
    mocker.patch.object(estimator, "_set_exp_time", return_value=image)

    assert await estimator(image) == image

    estimator._calc_exp_time.assert_called_once_with(image)
    estimator._set_exp_time.assert_called_once_with(image, 1.0)


def test_set_exp_time_lower(mocker):
    image = Image()
    mocker.patch.object(image, "set_meta")

    estimator = TestExpTimeEstimator(5., 10.)

    estimator._set_exp_time(image, 0.0)

    set_exp_time = image.set_meta.call_args[0][0].exptime
    assert set_exp_time == 5.0


def test_set_exp_time_upper(mocker):
    image = Image()
    mocker.patch.object(image, "set_meta")

    estimator = TestExpTimeEstimator(5., 10.)

    estimator._set_exp_time(image, 15.0)

    set_exp_time = image.set_meta.call_args[0][0].exptime
    assert set_exp_time == 10.0
