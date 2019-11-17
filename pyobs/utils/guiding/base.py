import logging

from pyobs.interfaces import ITelescope
from pyobs.utils.images import Image


log = logging.getLogger(__name__)


class BaseGuider:
    def __call__(self, image: Image, telescope: ITelescope):
        """Processes an image.

        Args:
            image: Image to process.
            telescope: Telescope to guide
        """
        raise NotImplementedError

    def reset(self):
        """Reset auto-guider."""
        raise NotImplementedError

    def is_loop_closed(self) -> bool:
        """Whether loop is closed."""
        raise NotImplementedError


__all__ = ['BaseGuider']
