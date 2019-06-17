from enum import Enum

from .interface import Interface


class IMotion(Interface):
    """
    Basic interface for all devices that move.

    There are no generic motion methods - these have to be defined in daughter
    interfaces.
    """

    class Status(Enum):
        """
        Enumerator for moving device status:
            - PARKED means that the device needs to be initialized or positioned or
              moved (depending upon the device; some devices don't need a formal
              initialization); presumedly, this is the safe "off" state.
            - INITIALIZING means that the device is transitioning from a PARKED state
              to an active state but is not yet fully operable.
            - unPARKED is either IDLE (operating but in no particular state) or
              POSITIONED (operating in a well-defined state)
            - SLEWING means that the device is moving to some targeted state (e.g.
              to POSITIONED or TRACKING) but has not yet arrived at that state
            - TRACKING means that the device is moving as commanded
        """
        ABORTING = 'aborting'
        ERROR = 'error'
        IDLE = 'idle'
        INITIALIZING = 'initializing'
        PARKING = 'parking'
        PARKED = 'parked'
        POSITIONED = 'positioned'
        SLEWING = 'slewing'
        TRACKING = 'tracking'
        UNKNOWN = 'unknown'

    def init(self, *args, **kwargs):
        """Initialize device.

        Raises:
            ValueError: If device could not be initialized.
        """
        raise NotImplementedError

    def park(self, *args, **kwargs):
        """Park device.

        Raises:
            ValueError: If device could not be parked.
        """
        raise NotImplementedError

    def get_motion_status(self, device: str = None) -> Status:
        """Returns current motion status.

        Args:
            device: Name of device to get status for, or None.

        Returns:
            A string from the Status enumerator.
        """
        raise NotImplementedError

    def stop_motion(self, device: str = None):
        """Stop the motion.

        Args:
            device: Name of device to stop, or None for all.
        """
        raise NotImplementedError


__all__ = ['IMotion']
