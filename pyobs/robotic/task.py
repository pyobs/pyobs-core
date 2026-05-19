from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any
from pydantic import Field

from pyobs.robotic.scheduler.targets import Target
from pyobs.robotic.scripts import Script

if TYPE_CHECKING:
    from pyobs.robotic.observationarchive import ObservationArchive
    from pyobs.robotic.taskarchive import TaskArchive

from pyobs.robotic.scheduler.constraints import Constraint
from pyobs.robotic.scheduler.merits import Merit
from pyobs.utils.serialization import BaseModel


@dataclass
class TaskData:
    task: Task
    observation_archive: ObservationArchive | None = None
    task_archive: TaskArchive | None = None


class Task(BaseModel):
    id: Any | None = None
    name: str = Field(default="")
    project: str = Field(default="")
    duration: float = Field(ge=0.0, le=84000.0, default=0.0)
    priority: float | None = Field(ge=0.0, le=9999.0, default=1.0)
    constraints: list[Constraint] = Field(default_factory=list)
    merits: list[Merit] = Field(default_factory=list)
    target: Target | None = None
    script: dict[str, Any] = Field(default_factory=dict)

    def __str__(self) -> str:
        s = f"Task {self.id}: {self.name} (duration: {self.duration}s"
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
            script = self.pyobs_model_validate(Script, self.script, by_alias=True)
            return await script.can_run(data)
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
        if self.script is not None:
            script = self.pyobs_model_validate(Script, self.script, by_alias=True)
            await script.run(data)

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


class Project(BaseModel):
    id: Any | None = None
    name: str = Field(default="")
    priority: float | None = Field(ge=0.0, le=9999.0, default=1.0)


__all__ = ["Task", "TaskData", "Project"]
