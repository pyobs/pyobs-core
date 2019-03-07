from .interface import *


class IStatus(Interface):
    """Base interface for all interfaces that have to provide some sort of status."""

    def status(self, *args, **kwargs) -> dict:
        """Returns status of object in form of a dictionary. See other interfaces for details."""
        raise NotImplementedError


__all__ = ['IStatus']
