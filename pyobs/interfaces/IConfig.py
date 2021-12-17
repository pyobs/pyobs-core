from abc import ABCMeta
from typing import Any, Dict, Tuple, List

from .interface import Interface


class IConfig(Interface, metaclass=ABCMeta):
    """The module allows access to some of its configuration options."""
    __module__ = 'pyobs.interfaces'

    async def get_config_caps(self, **kwargs: Any) -> Dict[str, Tuple[bool, bool, bool]]:
        """Returns dict of all config capabilities. First value is whether it has a getter, second is for the setter,
        third is for a list of possible options..

        Returns:
            Dict with config caps
        """
        raise NotImplementedError

    async def get_config_value(self, name: str, **kwargs: Any) -> Any:
        """Returns current value of config item with given name.

        Args:
            name: Name of config item.

        Returns:
            Current value.

        Raises:
            ValueError: If config item of given name does not exist.
        """
        raise NotImplementedError

    async def get_config_value_options(self, name: str, **kwargs: Any) -> List[str]:
        """Returns possible values for config item with given name.

        Args:
            name: Name of config item.

        Returns:
            Possible values.

        Raises:
            ValueError: If config item of given name does not exist.
        """
        raise NotImplementedError

    async def set_config_value(self, name: str, value: Any, **kwargs: Any) -> None:
        """Sets value of config item with given name.

        Args:
            name: Name of config item.
            value: New value.

        Raises:
            ValueError: If config item of given name does not exist or value is invalid.
        """
        raise NotImplementedError


__all__ = ['IConfig']
