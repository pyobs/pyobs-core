from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import Annotated, Any

from ..utils.enums import Unit
from ..utils.time import Time
from .IAbortable import IAbortable
from .IRunning import IRunning


@dataclass
class AutoFocusResult:
    focus: float
    focus_err: float


@dataclass
class AutoFocusPoint:  # AutoFocusStatus.points element
    focus: float
    value: float


@dataclass
class AutoFocusState:  # growing curve during autofocus run
    points: list[AutoFocusPoint] = field(default_factory=list)
    time: Time = field(default_factory=Time.now)


class IAutoFocus(IRunning, IAbortable, metaclass=ABCMeta):
    """The module can perform an autofocus."""

    __module__ = "pyobs.interfaces"

    state = AutoFocusState

    @abstractmethod
    async def auto_focus(
        self, count: int, step: float, exposure_time: Annotated[float, Unit.SECONDS], **kwargs: Any
    ) -> AutoFocusResult:
        """Perform an autofocus series.

        This method performs an autofocus series with "count" images on each side of the initial guess and the given
        step size. With count=3, step=1 and guess=10, this takes images at the following focus values:
        7, 8, 9, 10, 11, 12, 13

        Args:
            count: Number of images to take on each side of the initial guess. Should be an odd number.
            step: Step size.
            exposure_time: Exposure time for images.

        Returns:
            Result of autofocus.

        Raises:
            AbortedError: If the autofocus series was aborted.
            FocusError: If focus could not be obtained.
        """
        ...


__all__ = ["IAutoFocus", "AutoFocusResult", "AutoFocusPoint", "AutoFocusState"]
