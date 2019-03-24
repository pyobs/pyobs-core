from .IMotion import IMotion


class IRoof(IMotion):
    """Base interface for all observatory enclosures."""

    def open_roof(self, *args, **kwargs):
        """ Transition from PARKED to IDLE/POSITIONED """
        raise NotImplementedError

    def close_roof(self, *args, **kwargs):
        """ Transition from IDLE/POSITIONED/TRACKING/SLEWING to PARKED """
        raise NotImplementedError

    def halt_roof(self, *args, **kwargs):
        """ Transition from IDLE/POSITIONED/TRACKING/SLEWING to PARKED """
        raise NotImplementedError


__all__ = ['IRoof']
