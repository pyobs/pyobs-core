from typing import Any
from astroplan import Observer

from pyobs.interfaces.proxies import ITelescopeProxy
from pyobs.utils.threads import Future


class SkyFlatsBasePointing(object):
    """Base class for flat poinings."""
    __module__ = 'pyobs.utils.skyflats.pointing'

    def __init__(self, observer: Observer, *args: Any, **kwargs: Any):
        self.observer = observer

    def __call__(self, telescope: ITelescopeProxy) -> Future[None]:
        """Move telescope.

        Args:
            telescope: Telescope to use.

        Returns:
            Future for the movement call.
        """
        raise NotImplementedError

    def reset(self) -> None:
        """Reset pointing."""
        pass


__all__ = ['SkyFlatsBasePointing']
