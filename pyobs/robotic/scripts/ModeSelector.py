from typing import Any, Dict

from pyobs.robotic.scripts import Script


class ModeSelector(Script):
    """Script for running a mode selection."""

    __module__ = "pyobs.modules.robotic"

    def __init__(
            self,
            config: Dict[str, Any],
            **kwargs: Any,
    ):
        """Initialize a new ModeSelector.

        Args:
            script: Config for script to run.
        """

        Script.__init__(self, **kwargs)
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
