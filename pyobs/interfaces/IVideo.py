from __future__ import annotations

from abc import ABCMeta
from dataclasses import dataclass

from .IData import IData


class IVideo(IData, metaclass=ABCMeta):
    """The module controls a video streaming device."""

    __module__ = "pyobs.interfaces"

    @dataclass
    class Capabilities:
        url: str = ""


__all__ = ["IVideo"]
