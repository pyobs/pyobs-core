"""Shared relative-tolerance exposure-time matching/grouping.

Used by the archive's exptime filter (single-value tolerance match) and by
science_exptimes_for_night's night-exptime grouping (bucketing many raw values);
#832's per-exptime dark-master grouping reuses this rather than reimplementing it.
"""

from __future__ import annotations

import statistics
from collections.abc import Iterable


def exptimes_close(a: float, b: float, tolerance: float = 0.01) -> bool:
    """Whether two exposure times are within a relative tolerance of each other.

    Args:
        a: First exposure time, in seconds.
        b: Second exposure time, in seconds.
        tolerance: Relative tolerance, e.g. 0.01 for 1%.

    Returns:
        True if a and b are within tolerance of each other.
    """
    if a == b:
        return True
    if b == 0:
        return False
    return abs(a - b) <= tolerance * abs(b)


def group_exptimes(values: Iterable[float], tolerance: float = 0.01) -> list[float]:
    """Collapses exposure times within a relative tolerance of each other into groups.

    Args:
        values: Raw exposure times to group.
        tolerance: Relative tolerance for two values to belong to the same group.

    Returns:
        One representative exptime (the group's median) per group, sorted ascending.
    """
    groups: list[list[float]] = []
    for value in sorted(values):
        if groups and exptimes_close(value, statistics.median(groups[-1]), tolerance):
            groups[-1].append(value)
        else:
            groups.append([value])
    return [statistics.median(group) for group in groups]


__all__ = ["exptimes_close", "group_exptimes"]
