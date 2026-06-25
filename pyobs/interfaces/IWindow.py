from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from ..utils.time import Time
from .interface import Interface


class IWindow(Interface, metaclass=ABCMeta):
    """The camera supports windows, to be used together with :class:`~pyobs.interfaces.ICamera`."""

    __module__ = "pyobs.interfaces"

    @dataclass
    class State:
        x: int
        y: int
        width: int
        height: int
        time: Time = field(default_factory=Time.now)

    @dataclass
    class Capabilities:
        full_frame_x: int = 0
        full_frame_y: int = 0
        full_frame_width: int = 0
        full_frame_height: int = 0

    @abstractmethod
    async def get_full_frame(self, **kwargs: Any) -> IWindow.State:
        """Returns full size of CCD.

        Returns:
            Tuple with left, top, width, and height set.
        """
        ...

    @abstractmethod
    async def set_window(self, left: int, top: int, width: int, height: int, **kwargs: Any) -> None:
        """Set the camera window.

        Args:
            left: X offset of window.
            top: Y offset of window.
            width: Width of window.
            height: Height of window.

        Raises:
            ValueError: If window could not be set.
        """
        ...


__all__ = ["IWindow"]
