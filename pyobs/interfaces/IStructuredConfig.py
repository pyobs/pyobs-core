from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from ..utils.config_schema import ConfigFieldSchema, ConfigSchema  # re-export
from ..utils.time import Time
from .IConfig import ConfigScalar
from .interface import Interface

ConfigValue = ConfigScalar | list["ConfigValue"] | dict[str, "ConfigValue"]


@dataclass
class ConfigAppliedState:
    config: dict[str, ConfigValue]
    time: Time = field(default_factory=Time.now)


class IStructuredConfig(Interface, metaclass=ABCMeta):
    """The module accepts a whole structured (possibly nested) config
    object in one call, rather than per-field get/set (see IConfig for
    the per-field variant)."""

    __module__ = "pyobs.interfaces"

    capabilities = ConfigSchema
    state = ConfigAppliedState

    @abstractmethod
    async def set_config(self, config: dict[str, ConfigValue], **kwargs: Any) -> None:
        """Apply a full structured config to this module.

        Args:
            config: Nested dict matching this module's ConfigSchema
                (fetch via get_capabilities). Values are validated and
                deserialized into the module's internal config dataclass.

        Raises:
            ValueError: If config doesn't match the module's schema, or
                values fail validation.
        """
        ...


__all__ = ["IStructuredConfig", "ConfigAppliedState", "ConfigSchema", "ConfigFieldSchema"]
