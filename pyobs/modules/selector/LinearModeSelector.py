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
        config,
        **kwargs: Any,
    ):
        """Creates a new LinearModeSelector.

        Args:
        """
        Module.__init__(self, **kwargs)

        # check
        if self.comm is None:
            logging.warning("No comm module given!")
        self.basis = config['basis']

        self.modes    = config['modes']
        self.motor    = await self.proxy(config['motor'])

    @abstractmethod
    async def list_modes(self) -> List[str]:
        """List available modes.

        Returns:
            List of available modes.
        """
        return self.modes.keys()

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
        logging.warning('Neither photometry nor spectroscopy mode selected')
        return 'undefined'








    @abstractmethod
    async def init(self, **kwargs: Any) -> None:
        """Initialize device.

        Raises:
            InitError: If device could not be initialized.
        """
        log.error("Not implemented")

    @abstractmethod
    async def park(self, **kwargs: Any) -> None:
        """Park device.

        Raises:
            ParkError: If device could not be parked.
        """
        self.motor.move_to(self.basis)

    @abstractmethod
    async def get_motion_status(self, device: Optional[str] = None, **kwargs: Any) -> MotionStatus:
        """Returns current motion status.

        Args:
            device: Name of device to get status for, or None.

        Returns:
            A string from the Status enumerator.
        """
        log.error("Not implemented")

    @abstractmethod
    async def stop_motion(self, device: Optional[str] = None, **kwargs: Any) -> None:
        """Stop the motion.

        Args:
            device: Name of device to stop, or None for all.
        """
        log.error("Not implemented")
