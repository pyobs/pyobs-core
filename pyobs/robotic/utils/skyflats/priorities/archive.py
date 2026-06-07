import astropy.units as u
from astropy.time import TimeDelta

from pyobs.robotic.utils.archive import Archive
from pyobs.utils.enums import ImageType
from pyobs.utils.time import Time

from .base import SkyflatPriorities


class ArchiveSkyflatPriorities(SkyflatPriorities):
    """Calculate flat priorities from an archive."""

    __module__ = "pyobs.utils.skyflats.priorities"

    archive: Archive
    site: str
    instrument: str
    filter_names: list[str]
    binnings: list[int]

    model_config = {"arbitrary_types_allowed": True}

    async def __call__(self) -> dict[tuple[str, tuple[int, int]], float]:
        now = Time.now()
        frames = await self.archive.list_frames(
            start=now - TimeDelta(100 * u.day),
            end=now,
            site=self.site,
            instrument=self.instrument,
            image_type=ImageType.SKYFLAT,
            rlevel=1,
        )

        from_archive: dict[tuple[str | None, int | None], float] = {}
        for f in frames:
            prio = (now - f.dateobs).sec / 86400.0
            key = (f.filter_name, f.binning)
            if key not in from_archive or prio < from_archive[key]:
                from_archive[key] = prio

        priorities: dict[tuple[str, tuple[int, int]], float] = {}
        for fn in self.filter_names:
            for b in self.binnings:
                priorities[fn, (b, b)] = from_archive[fn, b] if (fn, b) in from_archive else 100.0

        return priorities


__all__ = ["ArchiveSkyflatPriorities"]
