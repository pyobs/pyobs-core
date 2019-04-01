from .IMotion import IMotion


class IRoof(IMotion):
    """Base interface for all observatory enclosures."""

    def open_roof(self, *args, **kwargs):
        """Open the roof."""
        raise NotImplementedError

    def close_roof(self, *args, **kwargs):
        """Close the roof."""
        raise NotImplementedError

    def halt_roof(self, *args, **kwargs):
        """Stop roof."""
        raise NotImplementedError


__all__ = ['IRoof']
