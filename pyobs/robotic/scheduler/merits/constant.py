from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from .merit import MERIT_FACTOR_KEY, Merit

if TYPE_CHECKING:
    from pyobs.robotic import Task
    from pyobs.utils.time import Time

    from ..dataprovider import DataProvider


class ConstantMerit(Merit):
    """Merit function that returns a constant value."""

    merit: float = Field(ge=0.0, le=100.0, default=1.0, json_schema_extra={MERIT_FACTOR_KEY: True})

    def max_value(self) -> float:
        return self.merit

    async def __call__(self, time: Time, task: Task, data: DataProvider) -> float:
        return self.merit


__all__ = ["ConstantMerit"]
