from __future__ import annotations

from abc import ABCMeta
from dataclasses import dataclass

from .IData import IData


@dataclass
class VideoCapabilities:
    video: str = ""


class IVideo(IData, metaclass=ABCMeta):
    """The module controls a video streaming device."""

    __module__ = "pyobs.interfaces"

    capabilities = VideoCapabilities


__all__ = ["IVideo", "VideoCapabilities"]
