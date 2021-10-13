from typing import Any, Dict, Tuple, List

from .interface import Interface


class IConfig(Interface):
    """The module allows access to some of its configuration options."""
    __module__ = 'pyobs.interfaces'

    def get_config_caps(self, *args, **kwargs) -> Dict[str, Tuple[bool, bool, bool]]:
        """Returns dict of all config capabilities. First value is whether it has a getter, second is for the setter,
        third is for a list of possible options..

        Returns:
            Dict with config caps
        """
        raise NotImplementedError

    def get_config_value(self, name: str, *args, **kwargs) -> Any:
        """Returns current value of config item with given name.

        Args:
            name: Name of config item.

        Returns:
            Current value.

        Raises:
            ValueError: If config item of given name does not exist.
        """
        raise NotImplementedError

    def get_config_value_options(self, name: str, *args, **kwargs) -> List:
        """Returns possible values for config item with given name.

        Args:
            name: Name of config item.

        Returns:
            Possible values.

        Raises:
            ValueError: If config item of given name does not exist.
        """
        raise NotImplementedError

    def set_config_value(self, name: str, value: Any, *args, **kwargs):
        """Sets value of config item with given name.

        Args:
            name: Name of config item.
            value: New value.

        Raises:
            ValueError: If config item of given name does not exist or value is invalid.
        """
        raise NotImplementedError


__all__ = ['IConfig']
