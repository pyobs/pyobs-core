# ls /dev | grep -E 'ttyUSB|ttyACM'


from zaber_motion import Units
from zaber_motion.ascii import Connection

from pyobs.modules import Module
from pyobs.modules.motor.basemotor import BaseMotor


class ZaberMotor(Module, BaseMotor):
    """Class for the Selection of Modus (Spectroscopy or Photometry)."""

    __module__ = "pyobs.modules.selector"

    def __init__(
        self,
        port,
        **kwargs: Any,
    ):
        """
        Creates a new BaseMotor.

        Args:
        """
        Module.__init__(self, **kwargs)

        # check
        if self.comm is None:
            logging.warning("No comm module given!")
        self.port = port

    def move_by(self, length, speed,
                length_unit=Units.ANGLE_DEGREES,
                speed_unit=Units.ANGULAR_VELOCITY_DEGREES_PER_SECOND):
        with Connection.open_serial_port(self.port) as connection:
            connection.enable_alerts()
            device = connection.detect_devices()[0] # TODO: raise xxx if len(device_list) is not 1 (0 -> no device found, >1 -> try to find correct one)
            axis = device.get_axis(1)
            axis.move_relative(length, length_unit, velocity=speed, velocity_unit=speed_unit)

    def check_position(self, position_unit=Units.ANGLE_DEGREES):
        with Connection.open_serial_port(self.port) as connection:
            connection.enable_alerts()
            device = connection.detect_devices()[0]
            axis = device.get_axis(1)
            return axis.get_position(unit=position_unit)
