import pandas as pd
import random
from pydantic import PrivateAttr
from typing import TYPE_CHECKING, Literal
from astropy.time import Time

from .picker import Picker

if TYPE_CHECKING:
    from pyobs.robotic.scheduler.targets import Target, SiderealTarget
    from pyobs.robotic import Task
    from pyobs.robotic.scheduler import DataProvider


class CsvPicker(Picker):
    """A helper class for picking a target from a list."""

    csv: str
    name_col: str = "name"
    ra_col: str = "ra"
    dec_col: str = "dec"
    frame: str = "icrs"
    ra_unit: Literal["deg", "hour"] = "deg"

    _dataframe: pd.DataFrame | None = PrivateAttr(default=None)

    async def __call__(self, time: Time, task: Task, data: DataProvider) -> Target | None:
        from pyobs.robotic.scheduler.targets import SiderealTarget

        # get data
        if self._dataframe is None:
            self._dataframe = await self.vfs.read_csv(self.csv)
            if self._dataframe is None:
                return None

        # sort constraints by cost and remove non-target rependent
        sorted_constraints = sorted(task.constraints, key=lambda c: c.cost)
        sorted_constraints = [c for c in sorted_constraints if c.target_dependent]

        # evaluate constraints for each candidate
        valid = []
        for _, row in self._dataframe.iterrows():
            ra = row[self.ra_col]
            if self.ra_unit == "hour":
                ra *= 15
            candidate = SiderealTarget(name=row[self.name_col], ra=ra, dec=row[self.dec_col])

            # create a temporary task with this candidate as target
            candidate_task = task.model_copy(update={"target": candidate})

            # check constraints
            valid_candidate = True
            for c in sorted_constraints:
                if not await c(time, candidate_task, data):
                    valid_candidate = False
                    break
            if valid_candidate:
                valid.append(candidate)

        if not valid:
            return None

        # pick random
        return random.choice(valid)


__all__ = ["CsvPicker"]
