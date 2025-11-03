import abc
from abc import ABCMeta
import astroplan

from pyobs.object import Object


class Constraint(Object, metaclass=ABCMeta):
    @abc.abstractmethod
    def to_astroplan(self) -> astroplan.Constraint: ...
