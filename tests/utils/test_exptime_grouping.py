from __future__ import annotations

import statistics
from dataclasses import dataclass

from pyobs.utils.exptime_grouping import exptimes_close, group_by_exptime, group_exptimes

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


# ── group_by_exptime ────────────────────────────────────────────────────────


@dataclass
class _Frame:
    name: str
    exptime: float


def test_group_by_exptime_groups_items_not_just_values() -> None:
    frames = [_Frame("a", 30.0), _Frame("b", 30.1), _Frame("c", 600.0)]

    groups = group_by_exptime(frames, key=lambda f: f.exptime)

    assert [f.name for f in groups[0]] == ["a", "b"]
    assert [f.name for f in groups[1]] == ["c"]


def test_group_by_exptime_preserves_key_sorted_order_within_group() -> None:
    frames = [_Frame("second", 30.1), _Frame("first", 29.9)]

    groups = group_by_exptime(frames, key=lambda f: f.exptime)

    assert [f.name for f in groups[0]] == ["first", "second"]


def test_group_by_exptime_empty_input() -> None:
    assert group_by_exptime([], key=lambda f: f.exptime) == []


def test_group_exptimes_is_group_by_exptime_collapsed_to_medians() -> None:
    values = [30.0, 30.1, 29.9, 600.0, 601.0]
    groups = group_by_exptime(values, key=lambda v: v)

    assert group_exptimes(values) == [statistics.median(g) for g in groups]
