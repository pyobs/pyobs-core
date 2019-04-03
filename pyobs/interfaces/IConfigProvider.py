from .interface import *


class IConfigProvider(Interface):
    def get_config(self, module: str, *args, **kwargs) -> dict:
        """Returns the config for the given module.

        Args:
            module: Name of module.

        Returns:
            Dictionary containing module config.
        """
        raise NotImplementedError


__all__ = ['IConfigProvider']
