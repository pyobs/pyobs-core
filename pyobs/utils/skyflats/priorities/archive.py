from typing import Any
from astropy.time import TimeDelta
import astropy.units as u

from pyobs.object import get_object
from pyobs.utils.archive import Archive
from pyobs.utils.time import Time
from .base import SkyflatPriorities
from ...enums import ImageType


class ArchiveSkyflatPriorities(SkyflatPriorities):
    """Calculate flat priorities from an archive."""

    __module__ = "pyobs.utils.skyflats.priorities"

    def __init__(
        self,
        archive: dict[str, Any] | Archive,
        site: str,
        instrument: str,
        filter_names: list[str],
        binnings: list[int],
        *args: Any,
        **kwargs: Any,
    ):
        SkyflatPriorities.__init__(self)
        self._archive = get_object(archive, Archive)
        self._filter_names = filter_names
        self._binnings = binnings
        self._site = site
        self._instrument = instrument

    async def __call__(self) -> dict[tuple[str, tuple[int, int]], float]:
        # get all reduced skyflat frames of the last 100 days
        now = Time.now()
        frames = await self._archive.list_frames(
            start=now - TimeDelta(100 * u.day),
            end=now,
            site=self._site,
            instrument=self._instrument,
            image_type=ImageType.SKYFLAT,
            rlevel=1,
        )

        # get priorities
        from_archive: dict[tuple[str | None, int | None], float] = {}
        for f in frames:
            # get number of days since flat was taken, which is our priority
            prio = (now - f.dateobs).sec / 86400.0

            # get key in priorities
            key = (f.filter_name, f.binning)

            # need to update it?
            if key not in from_archive or prio < from_archive[key]:
                from_archive[key] = prio

        # create priorities
        priorities: dict[tuple[str, tuple[int, int]], float] = {}
        for fn in self._filter_names:
            for b in self._binnings:
                priorities[fn, (b, b)] = from_archive[fn, b] if (fn, b) in from_archive else 100.0

        # finished
        return priorities


__all__ = ["ArchiveSkyflatPriorities"]
