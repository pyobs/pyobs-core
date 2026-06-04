from typing import TYPE_CHECKING

from pydantic import Field

from .merit import Merit

if TYPE_CHECKING:
    from astropy.time import Time
    from pyobs.robotic import Task
    from ..dataprovider import DataProvider


class ConstantMerit(Merit):
    """Merit function that returns a constant value."""

    merit: float = Field(ge=0.0, le=100.0, default=1.0)

    async def __call__(self, time: Time, task: Task, data: DataProvider) -> float:
        return self.merit


__all__ = ["ConstantMerit"]
