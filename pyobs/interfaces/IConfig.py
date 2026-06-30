from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from .interface import Interface


@dataclass
class ConfigCapabilities:
    caps: dict[str, tuple[bool, bool, bool]] = field(default_factory=dict)


class IConfig(Interface, metaclass=ABCMeta):
    """The module allows access to some of its configuration options."""

    __module__ = "pyobs.interfaces"

    capabilities = ConfigCapabilities

    @abstractmethod
    async def get_config_value(self, name: str, **kwargs: Any) -> Any:
        """Returns current value of config item with given name.

        Args:
            name: Name of config item.

        Returns:
            Current value.

        Raises:
            ValueError: If config item of given name does not exist.
        """
        ...

    @abstractmethod
    async def set_config_value(self, name: str, value: Any, **kwargs: Any) -> None:
        """Sets value of config item with given name.

        Args:
            name: Name of config item.
            value: New value.

        Raises:
            ValueError: If config item of given name does not exist or value is invalid.
        """
        ...


__all__ = ["IConfig", "ConfigCapabilities"]
