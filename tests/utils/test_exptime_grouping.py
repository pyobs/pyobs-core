from __future__ import annotations

from pyobs.utils.exptime_grouping import exptimes_close, group_exptimes

# ── exptimes_close ───────────────────────────────────────────────────────────


def test_exptimes_close_exact_match() -> None:
    assert exptimes_close(600.0, 600.0) is True


def test_exptimes_close_within_relative_tolerance() -> None:
    assert exptimes_close(605.0, 600.0, tolerance=0.01) is True


def test_exptimes_close_outside_relative_tolerance() -> None:
    assert exptimes_close(650.0, 600.0, tolerance=0.01) is False


def test_exptimes_close_zero_target_only_matches_zero() -> None:
    assert exptimes_close(0.0, 0.0) is True
    assert exptimes_close(1.0, 0.0) is False


def test_exptimes_close_is_symmetric() -> None:
    assert exptimes_close(100.0, 101.0, tolerance=0.01) == exptimes_close(101.0, 100.0, tolerance=0.01)
    assert exptimes_close(100.0, 101.01, tolerance=0.01) == exptimes_close(101.01, 100.0, tolerance=0.01)


# ── group_exptimes ───────────────────────────────────────────────────────────


def test_group_exptimes_collapses_near_duplicates() -> None:
    groups = group_exptimes([30.0, 30.1, 29.9, 600.0, 601.0])
    assert groups == [30.0, 600.5]


def test_group_exptimes_keeps_distinct_values_separate() -> None:
    groups = group_exptimes([10.0, 60.0, 600.0])
    assert groups == [10.0, 60.0, 600.0]


def test_group_exptimes_empty_input() -> None:
    assert group_exptimes([]) == []


def test_group_exptimes_single_value() -> None:
    assert group_exptimes([45.0]) == [45.0]
