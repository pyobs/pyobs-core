from __future__ import annotations
from typing import TYPE_CHECKING, Any
from astropy.units import Quantity
import astropy.units as u

from pyobs.object import Object, get_object
from pyobs.robotic.scheduler.targets import Target
from pyobs.robotic.scripts import Script

if TYPE_CHECKING:
    from pyobs.robotic.observationarchive import ObservationArchive
    from pyobs.robotic.taskrunner import TaskRunner
    from pyobs.robotic.taskarchive import TaskArchive

from pyobs.robotic.scheduler.constraints import Constraint
from pyobs.robotic.scheduler.merits import Merit


class Task(Object):

    def __init__(
        self,
        id: Any,
        name: str,
        duration: float,
        priority: float | None = None,
        config: dict[str, Any] | None = None,
        constraints: list[Constraint] | None = None,
        merits: list[Merit] | None = None,
        target: Target | None = None,
        script: Script | None = None,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self._id = id
        self._name = name
        self._duration = duration
        self._priority = priority
        self._config = config
        self._constraints = constraints
        self._merits = merits
        self._target = target
        self._script = script

    @staticmethod
    def from_dict(data: dict[str, Any]) -> Task:
        # get constraints
        constraints: list[Constraint] = []
        if "constraints" in data and data["constraints"] is not None:
            for constraint in data["constraints"]:
                constraints.append(get_object(constraint, Constraint))  # noqa: F821

        # get merits
        merits: list[Merit] = []
        if "merits" in data and data["merits"] is not None:
            for merit in data["merits"]:
                merits.append(get_object(merit, Merit))  # noqa: F821

        # get target
        target: Target | None = None
        if "target" in data and data["target"] is not None:
            target = get_object(data["target"], Target)  # noqa: F821

        # get script
        script: Script | None = None
        if "script" in data and data["script"] is not None:
            script = get_object(data["script"], Script)  # noqa: F821

        return Task(
            id=data["id"],
            name=data["name"],
            duration=data["duration"],
            priority=data["priority"] if "priority" in data else None,
            config=data["config"] if "config" in data else None,
            constraints=constraints,
            merits=merits,
            target=target,
            script=script,
        )

    def __str__(self) -> str:
        s = f"Task {self._id}: {self._name} (duration: {self._duration}"
        if self.priority is not None:
            s += f", priority: {self.priority}"
        if self.target is not None:
            s += f", target: {self.target.name}"
        s += ")"
        return s

    @property
    def id(self) -> Any:
        """ID of task."""
        return self._id

    @property
    def name(self) -> str:
        """Returns name of task."""
        return self._name

    @property
    def duration(self) -> Quantity:
        """Returns estimated duration of task in seconds."""
        return self._duration * u.second

    @property
    def priority(self) -> float:
        """Returns priority."""
        return self._priority if self._priority is not None else 0.0

    @property
    def config(self) -> dict[str, Any]:
        """Returns configuration."""
        return self._config if self._config is not None else {}

    @property
    def constraints(self) -> list[Constraint]:
        """Returns constraints."""
        return self._constraints if self._constraints is not None else []

    @property
    def merits(self) -> list[Merit]:
        """Returns merits."""
        return self._merits if self._merits is not None else []

    @property
    def target(self) -> Target | None:
        """Returns target."""
        return self._target

    @property
    def script(self) -> Script | None:
        """Returns script."""
        return self._script

    async def can_run(self, scripts: dict[str, Script] | None = None) -> bool:
        """Checks, whether this task could run now.

        Returns:
            True, if task can run now.
        """
        return True

    @property
    def can_start_late(self) -> bool:
        """Whether this tasks is allowed to start later than the user-set time, e.g. for flatfields.

        Returns:
            True, if task can start late.
        """
        return False

    async def run(
        self,
        task_runner: TaskRunner,
        observation_archive: ObservationArchive | None = None,
        task_archive: TaskArchive | None = None,
        scripts: dict[str, Script] | None = None,
    ) -> None:
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


__all__ = ["Task"]
