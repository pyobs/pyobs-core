from enum import Enum
from typing import Any, Optional

from .IReady import IReady
from pyobs.utils.enums import MotionStatus


class IMotion(IReady):
    """The module controls a device that can move."""
    __module__ = 'pyobs.interfaces'

    def init(self, **kwargs: Any) -> None:
        """Initialize device.

        Raises:
            ValueError: If device could not be initialized.
        """
        raise NotImplementedError

    def park(self, **kwargs: Any) -> None:
        """Park device.

        Raises:
            ValueError: If device could not be parked.
        """
        raise NotImplementedError

    def get_motion_status(self, device: Optional[str] = None, **kwargs: Any) -> MotionStatus:
        """Returns current motion status.

        Args:
            device: Name of device to get status for, or None.

        Returns:
            A string from the Status enumerator.
        """
        raise NotImplementedError

    def stop_motion(self, device: Optional[str] = None, **kwargs: Any) -> None:
        """Stop the motion.

        Args:
            device: Name of device to stop, or None for all.
        """
        raise NotImplementedError


__all__ = ['IMotion']
