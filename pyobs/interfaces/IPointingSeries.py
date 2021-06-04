from .interface import *


class IPointingSeries(Interface):
    """The module provides the interface for a device that initializes and finalizes a pointing series and adds points
    to it."""
    __module__ = 'pyobs.interfaces'

    def start_pointing_series(self, *args, **kwargs) -> str:
        """Start a new pointing series.

        Returns:
            A unique ID or filename, by which the series can be identified.
        """
        raise NotImplementedError

    def stop_pointing_series(self, *args, **kwargs):
        """Stop a pointing series."""
        raise NotImplementedError

    def add_pointing_measure(self, *args, **kwargs):
        """Add a new measurement to the pointing series."""
        raise NotImplementedError


__all__ = ['IPointingSeries']
