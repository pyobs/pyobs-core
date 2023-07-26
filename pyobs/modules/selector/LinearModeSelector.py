import logging
from abc import abstractmethod
from typing import Any, List, Optional

from pyobs.interfaces.IMode import IMode
from pyobs.modules import Module
from pyobs.utils.enums import MotionStatus


class LinearModeSelector(Module, IMode):
    """Class for the Selection of Modus with a linear Motor (e.g. Spectroscopy or Photometry)."""

    __module__ = "pyobs.modules.LinearModeSelector"

    def __init__(
        self,
        modes: dict,
        motor: str,
        **kwargs: Any,
    ):
        """Creates a new LinearModeSelector.
        Args:
            modes: dictionary of available modes in the form {name: position}
            motor: name of the motor used to set the modes
        """
        Module.__init__(self, **kwargs)

        # check
        if self.comm is None:
            logging.warning("No comm module given!")

        self.modes = modes
        self.motor = await self.proxy(motor)

    @abstractmethod
    async def list_modes(self) -> List[str]:
        """List available modes.

        Returns:
            List of available modes.
        """
        return list(self.modes.keys())

    @abstractmethod
    async def set_mode(self, mode: str) -> None:
        """Set the current mode.

        Args:
            mode: Name of mode to set.

        Raises:
            ValueError: If an invalid mode was given.
            MoveError: If mode selector cannot be moved.
        """
        if self.get_mode() == mode:
            logging.info('Mode %s already selected.', mode)
        logging.info('Moving mode selector ...')
        await self.motor.move_to(self.modes[mode])
        logging.info('Mode %s ready.', mode)
        return

    @abstractmethod
    async def get_mode(self) -> str:
        """Get currently set mode.

        Returns:
            Name of currently set mode.
        """
        pos_current = self.motor.check_position()
        for mode, mode_pos in self.modes.items():
            if pos_current == mode_pos:
                return mode
        logging.warning('None of the available modes selected. Available modes are: %s', self.list_modes())
        return 'undefined'








    @abstractmethod
    async def init(self, **kwargs: Any) -> None:
        """Initialize device.

        Raises:
            InitError: If device could not be initialized.
        """
        logging.error("Not implemented")

    @abstractmethod
    async def park(self, **kwargs: Any) -> None:
        """Park device.

        Raises:
            ParkError: If device could not be parked.
        """
        self.motor.to_basis()

    @abstractmethod
    async def get_motion_status(self, device: Optional[str] = None, **kwargs: Any) -> MotionStatus:
        """Returns current motion status.

        Args:
            device: Name of device to get status for, or None.

        Returns:
            A string from the Status enumerator.
        """
        logging.error("Not implemented")
        return MotionStatus.ERROR

    @abstractmethod
    async def stop_motion(self, device: Optional[str] = None, **kwargs: Any) -> None:
        """Stop the motion.

        Args:
            device: Name of device to stop, or None for all.
        """
        logging.error("Not implemented")
