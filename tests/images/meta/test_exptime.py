from pyobs.images.meta import ExpTime


def test_exp_time():
    exp_time = 1.0
    meta = ExpTime(exp_time)

    assert meta.exptime == exp_time
