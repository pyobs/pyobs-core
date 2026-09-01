from __future__ import annotations

from pyobs.robotic.utils.archive import Archive
from pyobs.utils.enums import ImageType
from pyobs.utils.exptime_grouping import group_exptimes


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

    return result


__all__ = ["science_exptimes_for_night"]
