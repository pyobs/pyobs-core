from typing import Any

from .interface import Interface


class IPointingSeries(Interface):
    """The module provides the interface for a device that initializes and finalizes a pointing series and adds points
    to it."""
    __module__ = 'pyobs.interfaces'

    def start_pointing_series(self, **kwargs: Any) -> str:
        """Start a new pointing series.

        Returns:
            A unique ID or filename, by which the series can be identified.
        """
        raise NotImplementedError

    def stop_pointing_series(self, **kwargs: Any) -> None:
        """Stop a pointing series."""
        raise NotImplementedError

    def add_pointing_measure(self, **kwargs: Any) -> None:
        """Add a new measurement to the pointing series."""
        raise NotImplementedError


__all__ = ['IPointingSeries']
