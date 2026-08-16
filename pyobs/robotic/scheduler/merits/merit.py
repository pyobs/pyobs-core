from __future__ import annotations

import inspect
from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, Any

from pyobs.utils.serialization import PolymorphicBaseModel, resolve_polymorphic_type_shorthand
from pyobs.utils.time import Time

if TYPE_CHECKING:
    from pyobs.robotic import Task

    from ..dataprovider import DataProvider


class Merit(PolymorphicBaseModel, metaclass=ABCMeta):
    """Merit class."""

    @abstractmethod
    async def __call__(self, time: Time, task: Task, data: DataProvider) -> float: ...

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


__all__ = ["Merit"]
