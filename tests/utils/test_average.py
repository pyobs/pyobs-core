from __future__ import annotations

import time

import pytest

from pyobs.utils.average import RollingTimeAverage


def test_average_empty_returns_none() -> None:
    avg = RollingTimeAverage(interval=10.0)
    assert avg.average() is None


def test_average_single_value() -> None:
    avg = RollingTimeAverage(interval=10.0)
    avg.add(5.0)
    assert avg.average() == pytest.approx(5.0)


def test_average_multiple_values() -> None:
    avg = RollingTimeAverage(interval=10.0)
    avg.add(2.0)
    avg.add(4.0)
    avg.add(6.0)
    assert avg.average() == pytest.approx(4.0)


def test_average_clears_old_values() -> None:
    """Values older than interval are excluded from average."""
    avg = RollingTimeAverage(interval=0.1)
    avg.add(100.0)
    time.sleep(0.15)
    avg.add(1.0)
    result = avg.average()
    assert result == pytest.approx(1.0)


def test_clear_resets_values() -> None:
    avg = RollingTimeAverage(interval=10.0)
    avg.add(5.0)
    avg.clear()
    assert avg.average() is None


def test_clear_resets_start_time() -> None:
    avg = RollingTimeAverage(interval=10.0)
    avg.add(5.0)
    t1 = avg._start_time
    avg.clear()
    t2 = avg._start_time
    assert t2 >= t1


def test_average_min_interval_none_when_no_old_values() -> None:
    """With min_interval, returns None if no values are older than min_interval."""
    avg = RollingTimeAverage(interval=10.0)
    avg.add(5.0)
    # all values are fresh — none older than min_interval=1s
    result = avg.average(min_interval=1.0)
    assert result is None


def test_average_min_interval_returns_when_old_values_exist() -> None:
    """With min_interval, returns average if there are values older than min_interval."""
    avg = RollingTimeAverage(interval=10.0)
    avg.add(5.0)
    time.sleep(0.15)
    avg.add(3.0)
    result = avg.average(min_interval=0.1)
    assert result is not None
    assert result == pytest.approx(4.0)  # average of 5.0 and 3.0


def test_average_includes_all_values_within_interval() -> None:
    """Only values within the rolling interval are included."""
    avg = RollingTimeAverage(interval=0.2)
    avg.add(10.0)
    time.sleep(0.1)
    avg.add(20.0)
    result = avg.average()
    assert result == pytest.approx(15.0)


def test_add_evicts_expired_values() -> None:
    """add() cleans up values older than interval."""
    avg = RollingTimeAverage(interval=0.1)
    avg.add(99.0)
    time.sleep(0.15)
    avg.add(1.0)
    assert len(avg._values) == 1
    assert avg._values[0][1] == 1.0
