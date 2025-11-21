from __future__ import annotations
import abc
from typing import Any
from astropy.coordinates import SkyCoord
import logging

from pyobs.object import Object

log = logging.getLogger(__name__)


class GridNode(Object, metaclass=abc.ABCMeta):
    """Abstract base class for grid nodes."""

    def __init__(self, log: bool = False, **kwargs: Any) -> None:
        Object.__init__(self, **kwargs)
        self._last: tuple[float, float] | SkyCoord | None = None
        self._log = log

    def __iter__(self) -> GridNode:
        return self

    @abc.abstractmethod
    def _get_next(self) -> tuple[float, float] | SkyCoord: ...

    def __next__(self) -> tuple[float, float] | SkyCoord:
        self._last = self._get_next()
        return self._last

    @abc.abstractmethod
    def __len__(self) -> int: ...

    @abc.abstractmethod
    def append_last(self) -> None: ...

    def log(self, point: tuple[float, float] | SkyCoord) -> None:
        if not self._log:
            return
        if isinstance(point, SkyCoord):
            if hasattr(point, "ra") and hasattr(point, "dec"):
                log.info(f"Picked point at {point.to_string('hmsdms', precision=1)}.")
            elif hasattr(point, "az") and hasattr(point, "alt"):
                log.info(f"Picked point at Alt={point.alt.degree:.2f}°, Az={point.az.degree:.2f}°.")

    @abc.abstractmethod
    def log_last(self) -> None: ...
