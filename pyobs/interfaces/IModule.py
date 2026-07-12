from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from typing import Any

from .interface import Interface


@dataclass
class ModuleLocation:
    longitude: float = 0.0
    latitude: float = 0.0
    elevation: float = 0.0
    timezone: str = "utc"


@dataclass
class ModuleCapabilities:
    label: str = ""
    version: str = ""
    location: ModuleLocation | None = None


class IModule(Interface, metaclass=ABCMeta):
    """The module is actually a module. Implemented by all modules."""

    __module__ = "pyobs.interfaces"

    capabilities = ModuleCapabilities

    @abstractmethod
    async def reset_error(self, **kwargs: Any) -> bool:
        """Reset error of module, if any."""
        ...

    @abstractmethod
    async def get_permitted_methods(self, **kwargs: Any) -> list[str]:
        """Returns names of all methods the calling module is allowed to invoke on this module."""
        ...


__all__ = ["IModule", "ModuleCapabilities", "ModuleLocation"]
