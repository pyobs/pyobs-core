from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from typing import Any

from pyobs.utils.enums import ModuleState

from .interface import Interface


class IModule(Interface, metaclass=ABCMeta):
    """The module is actually a module. Implemented by all modules."""

    __module__ = "pyobs.interfaces"

    @dataclass
    class Capabilities:
        version: str = ""
        label: str = ""

    @abstractmethod
    async def get_label(self, **kwargs: Any) -> str:
        """Returns label of module."""
        ...

    @abstractmethod
    async def get_version(self, **kwargs: Any) -> str:
        """Returns pyobs version of module."""
        ...

    @abstractmethod
    async def get_state(self, **kwargs: Any) -> ModuleState:
        """Returns current state of module."""
        ...

    @abstractmethod
    async def reset_error(self, **kwargs: Any) -> bool:
        """Reset error of module, if any."""
        ...

    @abstractmethod
    async def get_error_string(self, **kwargs: Any) -> str:
        """Returns description of error, if any."""
        ...


__all__ = ["IModule"]
