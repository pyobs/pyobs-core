from typing import Any
from astroplan import Observer

from pyobs.interfaces import ITelescope
from pyobs.object import Object
from pyobs.utils.threads import Future


class SkyFlatsBasePointing(Object):
    """Base class for flat poinings."""
    __module__ = 'pyobs.utils.skyflats.pointing'

    def __call__(self, telescope: ITelescope) -> Future[None]:
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
