from pyobs.modules.robotic._pointingseriesiterator import _LoopedRandomIterator


def test_iter() -> None:
    data = [1, 2]

    iterator = _LoopedRandomIterator(data)

    assert set(data) == {next(iterator), next(iterator)}  # Check first cycle
    assert set(data) == {next(iterator), next(iterator)}  # Check second cycle
