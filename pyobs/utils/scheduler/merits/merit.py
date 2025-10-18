from abc import ABCMeta, abstractmethod

from astroplan import Observer


class Merit(metaclass=ABCMeta):
    """Merit class."""

    def __init__(self, observer: Observer):
        self.observer = observer

    @abstractmethod
    def __call__(self, merit: float) -> float: ...

    @abstractmethod
    def _calculate_merit(self) -> float: ...


class MultiplicativeMerit(Merit):
    """Merit with multiple apertures."""

    def __call__(self, merit: float) -> float:
        return merit * self._calculate_merit()


__all__ = ["Merit"]
