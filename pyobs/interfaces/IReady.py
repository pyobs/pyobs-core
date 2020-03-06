from .interface import Interface


class IReady(Interface):
    """Interface for all devices that can be "not ready" for science and need to be initialized in some way."""

    def is_ready(self, *args, **kwargs) -> bool:
        """Returns the device is "ready", whatever that means for the specific device.

        Returns:
            Whether device is ready
        """
        raise NotImplementedError


__all__ = ['IReady']
