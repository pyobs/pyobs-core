from abc import ABCMeta

from pyobs.object import Object


class Target(Object, metaclass=ABCMeta):
    pass


__all__ = ["Target"]
