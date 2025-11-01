from __future__ import annotations
import abc
from typing import Any, TYPE_CHECKING
from .merit import Merit

if TYPE_CHECKING:
    from astropy.coordinates import SkyCoord
    from astropy.time import Time
    from pyobs.robotic import Task
    from ..dataprovider import DataProvider


class AvoidanceMerit(Merit, metaclass=abc.ABCMeta):
    """Base class for merit functions that work on the distance to a celestial object, e.g. sun or moon."""

    def __init__(self, impact: float = 1.0, stretch: float = 2.0, **kwargs: Any):
        super().__init__(**kwargs)
        self._impact = impact
        self._stretch = stretch

    def __call__(self, time: Time, task: Task, data: DataProvider) -> float:
        if task.target is None:
            return 1.0

        # target position
        target = task.target.coordinates(time)

        # position to avoid
        avoid = self._avoidance_position(time, data)

        # calculate distance
        dist = data.get_distance(target, avoid)

        # calculate merit
        return float(self._impact * dist.degree**self._stretch)

    @abc.abstractmethod
    def _avoidance_position(self, time: Time, data: DataProvider) -> SkyCoord: ...


__all__ = ["AvoidanceMerit"]
