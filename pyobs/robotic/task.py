from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any
from astroplan import Observer
from astropydantic import AstroPydanticQuantity  # type: ignore
from pydantic import BaseModel
import astropy.units as u

from pyobs.comm import Comm
from pyobs.robotic.scheduler.targets import Target
from pyobs.robotic.scripts import Script

if TYPE_CHECKING:
    from pyobs.robotic.observationarchive import ObservationArchive
    from pyobs.robotic.taskarchive import TaskArchive

from pyobs.robotic.scheduler.constraints import Constraint
from pyobs.robotic.scheduler.merits import Merit


@dataclass
class TaskData:
    task: Task
    observation_archive: ObservationArchive | None = None
    task_archive: TaskArchive | None = None
    observer: Observer | None = None
    comm: Comm | None = None


class Task(BaseModel):
    id: Any
    name: str
    duration: AstroPydanticQuantity[u.second]
    priority: float | None = None
    config: dict[str, Any] = {}
    constraints: list[Constraint] = []
    merits: list[Merit] = []
    target: Target | None = None
    script: Script | None = None

    def __str__(self) -> str:
        s = f"Task {self.id}: {self.name} (duration: {self.duration}"
        if self.priority is not None:
            s += f", priority: {self.priority}"
        if self.target is not None:
            s += f", target: {self.target.name}"
        s += ")"
        return s

    async def can_run(self, data: TaskData) -> bool:
        """Checks whether this task could run now.

        Returns:
            True, if the task can run now.
        """
        if self.script is not None:
            return await self.script.can_run(data)
        return True

    @property
    def can_start_late(self) -> bool:
        """Whether this tasks is allowed to start later than the user-set time, e.g. for flatfields.

        Returns:
            True, if task can start late.
        """
        return False

    async def run(self, data: TaskData) -> None:
        """Run a task"""
        ...

    def is_finished(self) -> bool:
        """Whether task is finished."""
        return False

    def get_fits_headers(self, namespaces: list[str] | None = None) -> dict[str, tuple[Any, str]]:
        """Returns FITS header for the current status of this module.

        Args:
            namespaces: If given, only return FITS headers for the given namespaces.

        Returns:
            Dictionary containing FITS headers.
        """
        return {}


__all__ = ["Task", "TaskData"]
