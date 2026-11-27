from __future__ import annotations

import inspect
import math
from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, Any

from pyobs.utils.serialization import PolymorphicBaseModel, resolve_polymorphic_type_shorthand
from pyobs.utils.time import Time

if TYPE_CHECKING:
    from pyobs.robotic import Task

    from ..dataprovider import DataProvider


MERIT_FACTOR_KEY = "x-pyobs-merit-factor"
"""JSON-schema key on a merit field whose value is (an upper bound of) the factor the merit returns,
so editors can bound it."""


class Merit(PolymorphicBaseModel, metaclass=ABCMeta):
    """Merit class."""

    @abstractmethod
    async def __call__(self, time: Time, task: Task, data: DataProvider) -> float: ...

    def max_value(self) -> float:
        """Largest value this merit can return with its current parameters.

        Merits are multiplied, so a value above 1 raises a task's ranking. Override in derived
        classes; the default (infinity) treats an undeclared merit as unbounded.
        """
        return math.inf

    @property
    def name(self) -> str:
        return self.__class__.__name__

    @staticmethod
    def create(config: Merit | dict[str, Any]) -> Merit:
        if isinstance(config, Merit):
            return config
        if "type" in config:
            from . import __all__ as merits

            resolve_polymorphic_type_shorthand(config, merits, "pyobs.robotic.scheduler.merits", "merit")

        obj = Merit.model_validate(config, by_alias=True)
        if isinstance(obj, Merit):
            return obj
        else:
            raise ValueError(f"Invalid merit config: {config}")

    @staticmethod
    def list() -> list[str]:
        from pyobs.robotic.scheduler import merits

        return [name for name, obj in inspect.getmembers(merits) if inspect.isclass(obj)]


__all__ = ["Merit", "MERIT_FACTOR_KEY"]
