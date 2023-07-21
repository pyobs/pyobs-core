import logging
from typing import Any

from pyobs.interfaces.IMotor import IMotor
from pyobs.modules import Module


class BaseMotor(Module, IMotor):
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


    def move_to(self, position) -> None:
        step = position - self.check_position()
        self.move_by(step)

    def move_by(self, length) -> None:
        ...

    def to_basis(self) -> None:
        self.move_to(self.basis)
        ...

    def check_position(self) -> float:
        ...
