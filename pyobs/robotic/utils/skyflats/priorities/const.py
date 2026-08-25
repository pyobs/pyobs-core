from pydantic import Field

from .base import SkyflatPriorities


class ConstSkyflatPriorities(SkyflatPriorities):
    """Constant flat priorities."""

    priorities: dict[tuple[str, tuple[int, int]], float] = Field(
        description="Fixed priority per (filter, binning) combination."
    )

    async def __call__(self) -> dict[tuple[str, tuple[int, int]], float]:
        return self.priorities


__all__ = ["ConstSkyflatPriorities"]
