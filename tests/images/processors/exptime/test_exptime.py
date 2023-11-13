from pyobs.images.processors.exptime import ExpTimeEstimator
from pyobs.images import Image


class TestExpTimeEstimator(ExpTimeEstimator):
    async def __call__(self, image: Image) -> Image:
        pass


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
