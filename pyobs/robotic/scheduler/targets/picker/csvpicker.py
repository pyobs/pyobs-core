import pandas as pd
import random
from pydantic import PrivateAttr
from typing import TYPE_CHECKING
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
    min_alt: float | None = None
    max_alt: float | None = None

    _dataframe: pd.DataFrame | None = PrivateAttr(default=None)

    async def __call__(self, time: Time, task: Task, data: DataProvider) -> Target | None:
        from pyobs.robotic.scheduler.targets import SiderealTarget

        # get data
        if self._dataframe is None:
            self._dataframe = await self.vfs.read_csv(self.csv)
            if self._dataframe is None:
                return None

        # evaluate constraints for each candidate
        valid = []
        for _, row in self._dataframe.iterrows():
            candidate = SiderealTarget(
                name=row[self.name_col].values[0], ra=row[self.ra_col].values[0], dec=row[self.dec_col].values[0]
            )

            # create a temporary task with this candidate as target
            candidate_task = task.model_copy(update={"target": candidate})

            if all(await c(time, candidate_task, data) for c in task.constraints):
                valid.append(candidate)

        if not valid:
            return None

        # pick random
        return random.choice(valid)


__all__ = ["CsvPicker"]
