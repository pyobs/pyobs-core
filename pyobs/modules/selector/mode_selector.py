import logging
from typing import Any

from pyobs.modules import Module

from zaber_motion import Units
from zaber_motion.ascii import Connection


class ModeSelector(Module):
    """Class for the Selection of Modus (Spectroscopy or Photometry)."""

    __module__ = "pyobs.modules.selector"

    def __init__(
        self,
        **kwargs: Any,
    ):
        """Creates a new ModusSelector.

        Args:
            modus_aim: Whether Spectroscopy ('spec') or Photometry ('phot') is wanted.
        """
        Module.__init__(self, **kwargs)

        # check
        if self.comm is None:
            logging.warning("No comm module given, will not be able to signal new images!")

        # store
        self._modi = {'spec': 100, 'phot': -100}  # provisional assignment of modus to position of motor, HOWEVER: spec at origin and phot at origin+x more realistic
        self._port = 'placeholder'  # ls /dev | grep -E 'ttyUSB|ttyACM' #TODO

    async def check_modus(self) -> str:
        with Connection.open_serial_port(self._port) as connection:
            connection.enable_alerts()
            device_list = connection.detect_devices()
            logging.info("Found %d devices", len(device_list))
            #TODO: raise xxx if len(device_list) is not 1 (0 -> no device found, >1 -> try to find correct one)

            device = device_list[0]

            axis = device.get_axis(1)
            pos_current = await axis.get_position()

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
        with Connection.open_serial_port(self._port) as connection:
            connection.enable_alerts()
            device_list = connection.detect_devices()
            logging.info("Found %d devices", len(device_list))
            #TODO: raise xxx if len(device_list) is not 1 (0 -> no device found, >1 -> try to find correct one)
            device = device_list[0]

            axis = device.get_axis(1)
            #if not axis.is_homed():
            #    axis.home()

            # Move to position assigned to aimed mode
            pos_aim = self._modi[mode_aim]
            pos_current = await axis.get_position()
            if pos_aim == pos_current:
                logging.info('Mode %s already selected.', mode_aim)
                return
            move_by = pos_aim - pos_current
            logging.info('Moving selector mirror ...')
            await axis.move_absolute(move_by, Units.LENGTH_MILLIMETRES)
        logging.info('Mode %s ready.', mode_aim)
        return
