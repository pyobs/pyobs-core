from typing import Any

from .interface import Interface


class IReady(Interface):
    """The module can be in a "not ready" state for science and need to be initialized in some way."""
    __module__ = 'pyobs.interfaces'

    async def is_ready(self, **kwargs: Any) -> bool:
        """Returns the device is "ready", whatever that means for the specific device.

        Returns:
            Whether device is ready
        """
        raise NotImplementedError


__all__ = ['IReady']
