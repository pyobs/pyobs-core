from astroplan import Observer

from pyobs.interfaces import ITelescope
from pyobs.utils.threads import Future


class SkyFlatsBasePointing:
    def __init__(self, observer: Observer, *args, **kwargs):
        self.observer = observer

    def __call__(self, telescope: ITelescope) -> Future:
        """Move telescope.

        Args:
            telescope: Telescope to use.

        Returns:
            Future for the movement call.
        """
        raise NotImplementedError


__all__ = ['SkyFlatsBasePointing']
