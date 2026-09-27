from __future__ import annotations

from abc import ABCMeta, abstractmethod
from collections.abc import Callable
from typing import Any, TypeVar

from .interface import Interface

F = TypeVar("F", bound=Callable[..., Any])


def default_reset(func: F) -> F:
    """Marks a base-class reset()/full_reset() that doesn't know driver-specific settings."""
    func.__pyobs_default_reset__ = True  # type: ignore[attr-defined]
    return func


class IResettable(Interface, metaclass=ABCMeta):
    """The module can reset itself to its defaults, per-acquisition settings only or completely."""

    __module__ = "pyobs.interfaces"

    @abstractmethod
    async def reset(self, **kwargs: Any) -> None:
        """Reset all per-acquisition settings to their defaults.

        Per-acquisition settings are the ones that only affect the next grab: exposure time,
        image type, binning, window, data pipeline, and driver-specific ones like gain. Settings
        that move hardware or change its thermal state (cooling setpoint, filter, focus, ...)
        are never touched.

        Raises:
            DeviceBusyError: If the device is currently exposing, or running a sequence or stack.
        """
        ...

    @abstractmethod
    async def full_reset(self, **kwargs: Any) -> None:
        """Reset the device completely to its configured defaults, hardware included.

        Does everything reset() does, plus hardware settings: cooling (enabled and setpoint
        from the module config) and any other driver-specific hardware state.

        Raises:
            DeviceBusyError: If the device is currently exposing, or running a sequence or stack.
        """
        ...


__all__ = ["IResettable", "default_reset"]
