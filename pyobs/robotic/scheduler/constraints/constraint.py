from __future__ import annotations

import inspect
from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, Any

import astroplan
import numpy as np
from astropy.coordinates import SkyCoord

from pyobs.object import Object
from pyobs.utils.serialization import PolymorphicBaseModel

if TYPE_CHECKING:
    from pyobs.robotic import Task
    from pyobs.utils.time import Time

    from ..dataprovider import DataProvider


class Constraint(PolymorphicBaseModel, metaclass=ABCMeta):
    cost: float = 1.0  # change in derived classes if needed
    target_dependent: bool = False  # change in derived classes if needed

    @abstractmethod
    def to_astroplan(self) -> astroplan.Constraint: ...

    @abstractmethod
    async def __call__(self, time: Time, task: Task, data: DataProvider) -> bool: ...

    @property
    def name(self) -> str:
        return self.__class__.__name__

    @staticmethod
    def create(obj: Object, config: Constraint | dict[str, Any]) -> Constraint:
        if isinstance(config, Constraint):
            return config
        if "type" in config:
            from . import __all__ as constraints

            constraints_lower = [c.lower() for c in constraints]
            try:
                idx = constraints_lower.index(config["type"].lower() + "constraint")
            except ValueError:
                raise ValueError(f"Invalid constraint type: {config['type']}")
            config["class"] = f"pyobs.robotic.scheduler.constraints.{constraints[idx]}"
        return obj.pyobs_model_validate(Constraint, config, by_alias=True)

    @staticmethod
    def list() -> list[str]:
        from pyobs.robotic.scheduler import constraints

        return [name for name, obj in inspect.getmembers(constraints) if inspect.isclass(obj)]

    async def filter_skycoord(self, time: Time, coords: SkyCoord, data: DataProvider) -> np.ndarray:
        """Returns a boolean mask of candidates passing this constraint.

        Default implementation passes all candidates. Override in target-dependent
        subclasses to vectorise the constraint evaluation across a SkyCoord array.

        Args:
            time: Time to evaluate constraint at.
            coords: Array of candidate coordinates.
            data: Data provider.

        Returns:
            Boolean numpy array, True for candidates that pass the constraint.
        """
        return np.ones(len(coords), dtype=bool)
