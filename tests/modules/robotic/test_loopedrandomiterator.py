from pyobs.modules.robotic._pointingseriesiterator import _LoopedRandomIterator


def test_iter() -> None:
    data = [1, 2]

    iterator = _LoopedRandomIterator(data)

    assert data == [next(iterator), next(iterator)]  # Check first cycle
    assert data == [next(iterator), next(iterator)]  # Check second cycle
