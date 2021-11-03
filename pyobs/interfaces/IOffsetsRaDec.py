from typing import Tuple, Any

from .interface import Interface


class IOffsetsRaDec(Interface):
    """The module supports RA/Dec offsets, usually combined with :class:`~pyobs.interfaces.ITelescope` and
    :class:`~pyobs.interfaces.IRaDec`."""
    __module__ = 'pyobs.interfaces'

    def set_offsets_radec(self, dra: float, ddec: float, **kwargs: Any) -> None:
        """Move an RA/Dec offset.

        Args:
            dra: RA offset in degrees.
            ddec: Dec offset in degrees.

        Raises:
            ValueError: If offset could not be set.
        """
        raise NotImplementedError

    def get_offsets_radec(self, **kwargs: Any) -> Tuple[float, float]:
        """Get RA/Dec offset.

        Returns:
            Tuple with RA and Dec offsets.
        """
        raise NotImplementedError


__all__ = ['IOffsetsRaDec']
