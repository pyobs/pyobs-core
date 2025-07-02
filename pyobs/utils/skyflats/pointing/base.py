from pyobs.interfaces import ITelescope
from pyobs.object import Object


class SkyFlatsBasePointing(Object):
    """Base class for flat poinings."""

    __module__ = "pyobs.utils.skyflats.pointing"

    async def __call__(self, telescope: ITelescope) -> None:
        """Move telescope.

        Args:
            telescope: Telescope to use.

        Returns:
            Future for the movement call.
        """
        raise NotImplementedError

    async def reset(self) -> None:
        """Reset pointing."""
        pass


__all__ = ["SkyFlatsBasePointing"]
