import inspect
from abc import ABCMeta, abstractmethod
import astroplan
from typing import TYPE_CHECKING, Any

from pyobs.object import Object
from pyobs.utils.serialization import PolymorphicBaseModel

if TYPE_CHECKING:
    from astropy.time import Time
    from ..dataprovider import DataProvider
    from pyobs.robotic import Task


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
