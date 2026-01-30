from __future__ import annotations
from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, Any

from pyobs.object import create_object
from pyobs.utils.serialization import SubClassBaseModel

if TYPE_CHECKING:
    from astropy.time import Time
    from ..dataprovider import DataProvider
    from pyobs.robotic import Task


class Merit(SubClassBaseModel, metaclass=ABCMeta):
    """Merit class."""

    @abstractmethod
    async def __call__(self, time: Time, task: Task, data: DataProvider) -> float: ...

    @staticmethod
    def create(config: Merit | dict[str, Any]) -> Merit:
        if isinstance(config, Merit):
            return config
        elif "type" in config:
            from . import __all__ as constraints

            if "." not in config["class"]:
                constraints_lower = [c.lower() for c in constraints]
                try:
                    idx = constraints_lower.index(config["class"].lower() + "merit")
                except ValueError:
                    raise ValueError(f"Invalid merit type: {config['class']}")

                config["class"] = f"pyobs.robotic.scheduler.merits.{constraints[idx]}"

            obj = create_object(config)
            if isinstance(obj, Merit):
                return obj
            else:
                raise ValueError(f"Invalid merit config: {config}")
        else:
            return Merit.model_validate(config, by_alias=True)


__all__ = ["Merit"]
