from __future__ import annotations
import abc
from typing import Any
from astropy.coordinates import SkyCoord
import logging

from pyobs.object import Object

log = logging.getLogger(__name__)


class GridNode(Object, metaclass=abc.ABCMeta):
    """Abstract base class for grid nodes.

    A GridNode implements the Python iterator protocol to produce a sequence
    of 2D points. Points can be either:
      - Tuples of floats representing (x, y) in degrees, or
      - astropy.coordinates.SkyCoord instances (e.g., in RA/Dec or Alt/Az frames).

    Subclasses must implement:
      - _get_next(): fetches the next point
      - __len__(): number of remaining points (if known)
      - append_last(): append the last yielded point back to the sequence
      - log_last(): log the last yielded point

    Logging is optional and can be enabled via the log flag. If enabled and the
    point is a SkyCoord, RA/Dec or Alt/Az are logged in human-readable form.
    """

    def __init__(self, log: bool = False, **kwargs: Any) -> None:
        """Initialize a GridNode.

        Args:
            log: If True, enable informational logging for picked points.
            **kwargs: Additional keyword arguments forwarded to Object.__init__().
        """
        Object.__init__(self, **kwargs)
        self._last: tuple[float, float] | SkyCoord | None = None
        self._log = log

    def __iter__(self) -> GridNode:
        """Return iterator self.

        Returns:
            The GridNode itself as an iterator.
        """
        return self

    @abc.abstractmethod
    def _get_next(self) -> tuple[float, float] | SkyCoord:
        """Return the next point in the sequence.

        Implementors must return either a (x, y) tuple of floats (degrees),
        or a SkyCoord instance.

        Returns:
            A point as (x, y) in degrees, or a SkyCoord.

        Raises:
            StopIteration: If there are no more points.
        """
        ...

    def __next__(self) -> tuple[float, float] | SkyCoord:
        """Return the next point, storing it as the last yielded value.

        Returns:
            A point as (x, y) in degrees, or a SkyCoord.

        Raises:
            StopIteration: If there are no more points.
        """
        self._last = self._get_next()
        return self._last

    @abc.abstractmethod
    def __len__(self) -> int:
        """Return the number of points remaining.

        Returns:
            Number of points remaining to be yielded.

        Note:
            If the size is not known, subclasses may return an estimate or 0.
        """
        ...

    @abc.abstractmethod
    def append_last(self) -> None:
        """Append the last yielded point back to the underlying sequence.

        This can be used to "re-queue" the most recently returned point.

        Raises:
            RuntimeError: If no last point exists to append.
        """
        ...

    def log(self, point: tuple[float, float] | SkyCoord) -> None:
        """Log a point if logging is enabled.

        For SkyCoord instances, logs RA/Dec in hmsdms if available, otherwise
        Alt/Az in degrees if available. No logging occurs if log flag is False.

        Args:
            point: The point to log; either a (x, y) tuple in degrees or a SkyCoord.
        """
        if not self._log:
            return
        if isinstance(point, SkyCoord):
            if hasattr(point, "ra") and hasattr(point, "dec"):
                log.info(f"Picked point at {point.to_string('hmsdms', precision=1)}.")
            elif hasattr(point, "az") and hasattr(point, "alt"):
                log.info(f"Picked point at Alt={point.alt.degree:.2f}°, Az={point.az.degree:.2f}°.")

    @abc.abstractmethod
    def log_last(self) -> None:
        """Log the last yielded point, if any.

        Implementations typically delegate to self.log(self._last).

        Raises:
            RuntimeError: If there is no last point to log.
        """
        ...
