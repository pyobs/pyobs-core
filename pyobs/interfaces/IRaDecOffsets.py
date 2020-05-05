from .interface import Interface


class IRaDecOffsets(Interface):
    """Interface for any device that supports offsets in RA/Dec."""

    def set_radec_offsets(self, dra: float, ddec: float, *args, **kwargs):
        """Move an RA/Dec offset.

        Args:
            dra: RA offset in degrees.
            ddec: Dec offset in degrees.

        Raises:
            ValueError: If offset could not be set.
        """
        raise NotImplementedError

    def get_radec_offsets(self, *args, **kwargs) -> (float, float):
        """Get RA/Dec offset.

        Returns:
            Tuple with RA and Dec offsets.
        """
        raise NotImplementedError


__all__ = ['IRaDecOffsets']
