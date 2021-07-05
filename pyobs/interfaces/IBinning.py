from typing import Tuple, List

from .interface import Interface


class IBinning(Interface):
    """The camera supports binning, to be used together with :class:`~pyobs.interfaces.ICamera`."""
    __module__ = 'pyobs.interfaces'

    def set_binning(self, x: int, y: int, *args, **kwargs):
        """Set the camera binning.

        Args:
            x: X binning.
            y: Y binning.

        Raises:
            ValueError: If binning could not be set.
        """
        raise NotImplementedError

    def get_binning(self, *args, **kwargs) -> Tuple[int, int]:
        """Returns the camera binning.

        Returns:
            Tuple with x and y.
        """
        raise NotImplementedError

    def list_binnings(self, *args, **kwargs) -> List[Tuple[int, int]]:
        """List available binnings.

        Returns:
            List of available binnings as (x, y) tuples.
        """
        raise NotImplementedError


__all__ = ['IBinning']
