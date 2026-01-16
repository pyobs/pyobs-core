from __future__ import annotations
from abc import ABCMeta, abstractmethod
import astroplan
from typing import TYPE_CHECKING, Any

from pyobs.object import create_object

if TYPE_CHECKING:
    from astropy.time import Time
    from ..dataprovider import DataProvider
    from pyobs.robotic import Task


class Constraint(metaclass=ABCMeta):
    @abstractmethod
    def to_astroplan(self) -> astroplan.Constraint: ...

    @abstractmethod
    async def __call__(self, time: Time, task: Task, data: DataProvider) -> bool: ...

    @staticmethod
    def create(config: Constraint | dict[str, Any]) -> Constraint:
        if isinstance(config, Constraint):
            return config
        else:
            from . import __all__ as constraints

            constraints_lower = [c.lower() for c in constraints]
            try:
                idx = constraints_lower.index(config["type"].lower() + "constraint")
            except ValueError:
                raise ValueError(f"Invalid constraint type: {config['type']}")

            config["class"] = f"pyobs.robotic.scheduler.constraints.{constraints[idx]}"
            obj = create_object(config)
            if isinstance(obj, Constraint):
                return obj
            else:
                raise ValueError(f"Invalid constraint config: {config}")
