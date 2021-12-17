import logging
from typing import Any, TypeVar, Optional, List, Dict

from pyobs.object import Object
from pyobs.robotic import TaskArchive

log = logging.getLogger(__name__)


ProxyClass = TypeVar('ProxyClass')


class Script(Object):
    def __init__(self, configuration: Any, task_archive: TaskArchive, **kwargs: Any):
        """Init Script.

        Args:
            comm: Comm object to use
            observer: Observer to use
        """
        Object.__init__(self, **kwargs)

        # store
        self.exptime_done: float = 0.
        self.configuration = configuration
        self.task_archive = task_archive

    async def can_run(self) -> bool:
        """Whether this config can currently run."""
        raise NotImplementedError

    async def run(self) -> None:
        """Run script.

        Raises:
            InterruptedError: If interrupted
        """
        raise NotImplementedError

    def get_fits_headers(self, namespaces: Optional[List[str]] = None) -> Dict[str, Any]:
        """Returns FITS header for the current status of this module.

        Args:
            namespaces: If given, only return FITS headers for the given namespaces.

        Returns:
            Dictionary containing FITS headers.
        """
        return {}


__all__ = ['Script']
