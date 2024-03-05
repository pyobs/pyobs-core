from abc import ABCMeta, abstractmethod
from typing import List, Tuple

from astropy.table import QTable

from pyobs.images import Image


class _PhotometryCalculator(metaclass=ABCMeta):
    """Abstract class for photometry calculators."""

    @property
    @abstractmethod
    def catalog(self) -> QTable:
        ...

    @abstractmethod
    def set_data(self, image: Image):
        ...

    @abstractmethod
    def __call__(self, diameter: int):
        ...
