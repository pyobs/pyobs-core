from typing import Any, Dict

from pyobs.robotic.scripts import Script


class BaseMotor(Module, IMode):
    """Class for the Selection of Modus (Spectroscopy or Photometry)."""

    __module__ = "pyobs.modules.selector"

    def __init__(
        self,
        basis,
        **kwargs: Any,
    ):
        """Creates a new BaseMotor.

        Args:
        """
        Module.__init__(self, **kwargs)

        # check
        if self.comm is None:
            logging.warning("No comm module given!")
        self.basis = basis

        self.modi     = config['modi']
        self.motor    = await self.proxy(config['motor'])
        self.mode_aim = config['mode_aim']

    async def check_modus(self) -> str:
        pos_current = self.motor.check_position()

        if pos_current == self.modi['spec']:
            return 'spec'
        elif pos_current == self.modi['phot']:
            return 'phot'
        else:
            logging.warning('Neither photometry nor spectroscopy mode selected')
            return 'nomode'

    async def change_mode(self, mode_aim) -> None:
        """
        Args:
            modus_aim: Whether Spectroscopy ('spec') or Photometry ('phot') is wanted.
        """
        if self.check_mode() == mode_aim:
            logging.info('Mode %s already selected.', mode_aim)
        logging.info('Moving selector mirror ...')
        await self.motor.move_to(self.modi[mode_aim])
        logging.info('Mode %s ready.', mode_aim)
        return



    @abstractmethod
    async def list_modes(self, **kwargs: Any) -> List[str]:
        """List available modes.

        Returns:
            List of available modes.
        """
        ...

    @abstractmethod
    async def set_mode(self, mode_name: str, **kwargs: Any) -> None:
        """Set the current mode.

        Args:
            mode_name: Name of mode to set.

        Raises:
            ValueError: If an invalid mode was given.
            MoveError: If mode wheel cannot be moved.
        """
        ...

    @abstractmethod
    async def get_mode(self, **kwargs: Any) -> str:
        """Get currently set mode.

        Returns:
            Name of currently set mode.
        """
        ...
