"""Shared relative-tolerance exposure-time matching/grouping.

Used by the archive's exptime filter (single-value tolerance match), by
science_exptimes_for_night's night-exptime grouping (bucketing many raw values), and by
Reduction's per-exptime dark-master grouping (bucketing raw dark frames, not bare floats).
"""

from __future__ import annotations

import statistics
from collections.abc import Callable, Iterable
from typing import TypeVar

T = TypeVar("T")


def exptimes_close(a: float, b: float, tolerance: float = 0.01) -> bool:
    """Whether two exposure times are within a relative tolerance of each other.

    Symmetric: the tolerance is relative to whichever of a/b is larger, so
    exptimes_close(a, b, t) == exptimes_close(b, a, t) always.

    Args:
        a: First exposure time, in seconds.
        b: Second exposure time, in seconds.
        tolerance: Relative tolerance, e.g. 0.01 for 1%.

    Returns:
        True if a and b are within tolerance of each other.
    """
    if a == b:
        return True
    return abs(a - b) <= tolerance * max(abs(a), abs(b))


def group_by_exptime(items: Iterable[T], key: Callable[[T], float], tolerance: float = 0.01) -> list[list[T]]:
    """Groups arbitrary items by an exptime-valued key within a relative tolerance.

    A single left-to-right pass over the items sorted by key: each item joins the previous
    group if its key is within tolerance of that group's current median key, else starts a new
    group. This is not a transitive-closure/clustering guarantee -- e.g. grouping keys
    [100.0, 100.9, 101.8] at 1% tolerance can split 100.9 and 101.8 into different groups even
    though they're pairwise within tolerance, because the group's median drifts as items are
    added. Fine for the discrete, well-separated exptimes real detectors actually use; a caller
    that needs a stronger (union-find) grouping guarantee should not rely on this.

    Args:
        items: Items to group.
        key: Extracts the exposure time (seconds) to group each item by.
        tolerance: Relative tolerance for two items to belong to the same group.

    Returns:
        Groups of items, in ascending order of the group's median key. Each group preserves
        the relative order its items had in the (key-sorted) input.
    """
    groups: list[list[T]] = []
    for item in sorted(items, key=key):
        if groups and exptimes_close(key(item), statistics.median(key(i) for i in groups[-1]), tolerance):
            groups[-1].append(item)
        else:
            groups.append([item])
    return groups


def group_exptimes(values: Iterable[float], tolerance: float = 0.01) -> list[float]:
    """Collapses exposure times within a relative tolerance of each other into groups.

    See group_by_exptime for the grouping algorithm and its (non-transitive) guarantees.

    Args:
        values: Raw exposure times to group.
        tolerance: Relative tolerance for two values to belong to the same group.

    Returns:
        One representative exptime (the group's median) per group, sorted ascending.
    """
    return [statistics.median(group) for group in group_by_exptime(values, key=lambda v: v, tolerance=tolerance)]


__all__ = ["exptimes_close", "group_by_exptime", "group_exptimes"]
