from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from typing import Any

from .interface import Interface


class IModule(Interface, metaclass=ABCMeta):
    """The module is actually a module. Implemented by all modules."""

    __module__ = "pyobs.interfaces"

    @dataclass
    class Capabilities:
        version: str = ""
        label: str = ""

    @abstractmethod
    async def reset_error(self, **kwargs: Any) -> bool:
        """Reset error of module, if any."""
        ...


__all__ = ["IModule"]
