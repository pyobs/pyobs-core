from __future__ import annotations

import time as _time

from pyobs.robotic.utils.archive import Archive
from pyobs.utils.enums import ImageType
from pyobs.utils.exptime_grouping import group_exptimes

# Task.create_script() re-validates a Script (and any nested Archive field) fresh from its raw
# config dict on every call -- can_run()/estimate_duration() never see the same Archive instance
# twice, so caching can't key on archive identity. Keying on (site, night, ...) instead lets
# DarkBiasScript's can_run() (async) warm this once per scheduling pass and estimate_duration()
# (sync, can't query the archive itself) read the cached result moments later.
_CACHE_TTL = 300.0  # seconds

_CacheKey = tuple[str, str, float, float | None]
_CacheEntry = tuple[float, dict[tuple[str, str], list[float]]]
_cache: dict[_CacheKey, _CacheEntry] = {}


def _cache_key(site: str, night: str, tolerance: float, min_exptime: float | None) -> _CacheKey:
    return site, night, tolerance, min_exptime


async def science_exptimes_for_night(
    archive: Archive,
    site: str,
    night: str,
    tolerance: float = 0.01,
    min_exptime: float | None = 5.0,
) -> dict[tuple[str, str], list[float]]:
    """Derives the distinct exposure times science frames used on a given night.

    Used to decide which exptimes a morning DarkBiasScript run should take darks at, so
    calibration masters exist for the exptimes actually needed rather than one fixed value.
    Caches its result for a few minutes per (site, night, tolerance, min_exptime), so repeated
    calls within one scheduling pass don't re-query the archive.

    Args:
        archive: Archive to list the night's OBJECT frames from.
        site: Site code to filter frames by.
        night: Night to derive exptimes for, in Archive.list_frames(night=...)'s format.
        tolerance: Relative tolerance for collapsing near-duplicate exptimes into one group.
        min_exptime: Exptimes below this are dropped entirely before grouping -- per ADR
            0015's dark_min_exptime, calibration treats them as bias-only and never needs a
            dark master for them. Pass 0 or None to keep every exptime.

    Returns:
        Distinct, tolerance-grouped science exptimes, keyed per (instrument, binning) --
        mirrors the per-combination looping Reduction.__call__ does for calibration masters.
    """
    key = _cache_key(site, night, tolerance, min_exptime)
    cached = _cache.get(key)
    now = _time.monotonic()
    if cached is not None and now - cached[0] < _CACHE_TTL:
        return cached[1]

    options = await archive.list_options(night=night, site=site, image_type=ImageType.OBJECT, rlevel=0)

    result: dict[tuple[str, str], list[float]] = {}
    for instrument in options.get("instruments", []):
        for binning in options.get("binnings", []):
            frames = await archive.list_frames(
                night=night,
                site=site,
                instrument=instrument,
                binning=binning,
                image_type=ImageType.OBJECT,
                rlevel=0,
            )
            raw_exptimes = [f.exptime for f in frames if f.exptime is not None]
            if min_exptime:
                raw_exptimes = [e for e in raw_exptimes if e >= min_exptime]
            if raw_exptimes:
                result[instrument, binning] = group_exptimes(raw_exptimes, tolerance)

    _cache[key] = (now, result)
    return result


def clear_cache() -> None:
    """Clears science_exptimes_for_night's cache. For tests; production code relies on the TTL."""
    _cache.clear()


def peek_cached_science_exptimes_for_night(
    site: str,
    night: str,
    tolerance: float = 0.01,
    min_exptime: float | None = 5.0,
) -> dict[tuple[str, str], list[float]] | None:
    """Synchronous, cache-only lookup for science_exptimes_for_night's result.

    Never queries the archive. Returns None if nothing has been cached yet for this key (no
    prior science_exptimes_for_night() call) or the cached entry has expired. Used by
    DarkBiasScript.estimate_duration(), which is sync and can't await the real query itself.
    """
    cached = _cache.get(_cache_key(site, night, tolerance, min_exptime))
    if cached is None or _time.monotonic() - cached[0] >= _CACHE_TTL:
        return None
    return cached[1]


__all__ = ["science_exptimes_for_night", "peek_cached_science_exptimes_for_night", "clear_cache"]
