from __future__ import annotations

import inspect
from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, Any
from astropy.time import Time

from pyobs.utils.serialization import SubClassBaseModel

if TYPE_CHECKING:
    from ..dataprovider import DataProvider
    from pyobs.robotic import Task


class Merit(SubClassBaseModel, metaclass=ABCMeta):
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
        elif "type" in config:
            from . import __all__ as constraints

            if "." not in config["type"]:
                constraints_lower = [c.lower() for c in constraints]
                try:
                    idx = constraints_lower.index(config["type"].lower() + "merit")
                except ValueError:
                    raise ValueError(f"Invalid merit type: {config['type']}")

                config["class"] = f"pyobs.robotic.scheduler.merits.{constraints[idx]}"

            obj = Merit.model_validate(config, by_alias=True)
            if isinstance(obj, Merit):
                return obj
            else:
                raise ValueError(f"Invalid merit config: {config}")
        else:
            return Merit.model_validate(config, by_alias=True)

    @staticmethod
    def list() -> list[str]:
        from pyobs.robotic.scheduler import merits

        return [name for name, obj in inspect.getmembers(merits) if inspect.isclass(obj)]


__all__ = ["Merit"]
