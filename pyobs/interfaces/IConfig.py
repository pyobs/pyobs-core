from typing import Any, Dict, Tuple

from .interface import Interface


class IConfig(Interface):
    """Interface for getting/setting values that were configured in the YAML file."""

    def get_config_options(self, *args, **kwargs) -> Dict[str, Tuple[bool, bool]]:
        """Returns dict of all config options. First value is whether it has a getter, second is for the setter.

        Returns:
            Dict with config options
        """
        raise NotImplementedError

    def get_config_value(self, name: str, *args, **kwargs) -> Any:
        """Returns current value of config item with given name.

        Args:
            name: Name of config item.

        Returns:
            Current value.

        Raises:
            ValueError if config item of given name does not exist.
        """
        raise NotImplementedError

    def set_config_value(self, name: str, value: Any, *args, **kwargs):
        """Sets value of config item with given name.

        Args:
            name: Name of config item.
            value: New value.

        Raises:
            ValueError if config item of given name does not exist or value is invalid.
        """
        raise NotImplementedError


__all__ = ['IConfig']
