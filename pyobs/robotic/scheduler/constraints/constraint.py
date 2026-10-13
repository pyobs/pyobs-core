from __future__ import annotations

import inspect
from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, Any, ClassVar

import astroplan
import numpy as np
from astropy.coordinates import SkyCoord

from pyobs.interfaces import FitsHeaderEntry
from pyobs.object import Object
from pyobs.utils.serialization import PolymorphicBaseModel, resolve_polymorphic_type_shorthand

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

            resolve_polymorphic_type_shorthand(config, constraints, "pyobs.robotic.scheduler.constraints", "constraint")
        return obj.pyobs_model_validate(Constraint, config, by_alias=True)

    @staticmethod
    def list() -> list[str]:
        from pyobs.robotic.scheduler import constraints

        return [name for name, obj in inspect.getmembers(constraints) if inspect.isclass(obj)]

    req_token: ClassVar[str | None] = None
    """Token of this constraint type in its `HIERARCH REQ <TOKEN> <FIELD>` header cards, e.g. `"AIRMASS"`. Constraints
    without a token write nothing to the header."""

    def req_fields(self) -> dict[str, tuple[int | float | str, str]]:
        """Values of this constraint for the FITS header, by field name (`"MAX"`), with a short comment each.

        Together with `req_token` this records what a frame was asked for. The whole card (key, value and comment)
        has to fit into 80 characters, so keep comments short or empty.
        """
        return {}

    def get_fits_headers(self, index: int) -> dict[str, FitsHeaderEntry]:
        """FITS header cards that record this constraint as part of what a frame was asked for.

        Args:
            index: 1 for the first constraint of this type in a task, 2 for the second, and so on. Later ones get the
                number on the token: `HIERARCH REQ SUNALT MAX`, `HIERARCH REQ SUNALT2 MAX`.

        Returns:
            Dictionary of header cards, empty if the constraint declares no `req_token`.
        """
        if self.req_token is None:
            return {}
        token = self.req_token if index <= 1 else f"{self.req_token}{index}"
        return {
            f"HIERARCH REQ {token} {field}": FitsHeaderEntry(value, comment)
            for field, (value, comment) in self.req_fields().items()
        }

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
