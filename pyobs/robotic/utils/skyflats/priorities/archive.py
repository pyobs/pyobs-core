import astropy.units as u
from astropy.time import TimeDelta
from pydantic import Field

from pyobs.robotic.utils.archive import Archive
from pyobs.utils.enums import ImageType
from pyobs.utils.time import Time

from .base import SkyflatPriorities


class ArchiveSkyflatPriorities(SkyflatPriorities):
    """Calculate flat priorities from an archive."""

    archive: Archive = Field(description="Archive to query for the timestamp of the last flat per filter/binning.")
    site: str = Field(description="Site code to filter archive frames by.")
    instrument: str = Field(description="Instrument code to filter archive frames by.")
    filter_names: list[str] = Field(description="Filters to compute priorities for.")
    binnings: list[int] = Field(description="Binnings (as N for NxN) to compute priorities for.")

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
