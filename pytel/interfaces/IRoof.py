from .IMotionDevice import IMotionDevice


class IRoof(IMotionDevice):
    """
    Base interface for all observatory enclosures.

    Other interfaces to be implemented:
        IStatus
            Status
    """

    def open_roof(self, *args, **kwargs) -> bool:
        """ Transition from PARKED to IDLE/POSITIONED """
        raise NotImplementedError

    def close_roof(self, *args, **kwargs) -> bool:
        """ Transition from IDLE/POSITIONED/TRACKING/SLEWING to PARKED """
        raise NotImplementedError

    def halt_roof(self, *args, **kwargs) -> bool:
        """ Transition from IDLE/POSITIONED/TRACKING/SLEWING to PARKED """
        raise NotImplementedError


__all__ = ['IRoof']
