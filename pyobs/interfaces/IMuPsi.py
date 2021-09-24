from typing import Tuple

from .interface import Interface


class IMuPsi(Interface):
    """The module can move to Mu/Psi coordinates, usually combined with :class:`~pyobs.interfaces.ITelescope`."""
    __module__ = 'pyobs.interfaces'

    def move_mupsi(self, mu: float, psi: float, *args, **kwargs):
        """Starts tracking on given coordinates.

        Args:
            mu: Mu in deg to track.
            psi: Psi in deg to track.

        Raises:
            ValueError: If device could not track.
        """
        raise NotImplementedError

    def get_mupsi(self, *args, **kwargs) -> Tuple[float, float]:
        """Returns current Mu and Psi position.

        Returns:
            Tuple of current Mu and Psi  in degrees.
        """
        raise NotImplementedError


__all__ = ['IMuPsi']
