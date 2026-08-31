from __future__ import annotations

from abc import ABCMeta
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from ..utils.time import Time
from .IStartStop import IStartStop

if TYPE_CHECKING:
    from ..robotic.observation import Observation


@dataclass
class RoboticTask:
    id: Any
    name: str
    target: str | None = None  # target name, resolved if available
    start: Time | None = None  # planned start (next) / actual start (current)
    end: Time | None = None  # planned end / ETA
    obsnum: str | None = None  # "20260810-001" once assigned by the executor
    # ObservationState value (e.g. "in_progress"), kept as a plain str rather than
    # pyobs.robotic.observation.ObservationState: pyobs.interfaces must not depend on
    # pyobs.robotic (which itself depends on pyobs.interfaces), or module import order decides
    # whether it works.
    state: str | None = None
    priority: float | None = None

    @classmethod
    def from_observation(cls, observation: Observation) -> RoboticTask:
        """Build a wire-sized task summary from a full `Observation` record."""
        return cls(
            id=observation.task.id,
            name=observation.task.name,
            target=observation.target.name if observation.target is not None else None,
            start=Time(observation.start),
            end=Time(observation.end),
            obsnum=observation.obsnum,
            state=observation.state.value,
            priority=observation.priority,
        )


@dataclass
class RoboticState:
    current: RoboticTask | None = None
    next: RoboticTask | None = None  # immediate next observation to run
    cant_run_reason: str | None = None  # from TaskRunner.cant_run_reason(), for `next`
    time: Time = field(default_factory=Time.now)


class IRobotic(IStartStop, metaclass=ABCMeta):
    """The module executes a schedule of tasks (e.g. Mastermind)."""

    __module__ = "pyobs.interfaces"

    state = RoboticState


__all__ = ["IRobotic", "RoboticTask", "RoboticState"]
