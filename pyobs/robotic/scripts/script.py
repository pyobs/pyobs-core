from __future__ import annotations
import logging
from typing import Any, TypeVar, TYPE_CHECKING

from pyobs.object import Object

if TYPE_CHECKING:
    from pyobs.robotic import TaskSchedule, TaskRunner, TaskArchive

log = logging.getLogger(__name__)


ProxyClass = TypeVar("ProxyClass")


class Script(Object):
    def __init__(self, configuration: dict[str, Any] | None = None, **kwargs: Any):
        """Init Script.

        Args:
            comm: Comm object to use
            observer: Observer to use
        """
        Object.__init__(self, **kwargs)

        # store
        self.exptime_done: float = 0.0
        self.configuration = {} if configuration is None else configuration

    async def can_run(self) -> bool:
        """Whether this config can currently run."""
        raise NotImplementedError

    async def run(
        self,
        task_runner: TaskRunner | None = None,
        task_schedule: TaskSchedule | None = None,
        task_archive: TaskArchive | None = None,
    ) -> None:
        """Run script.

        Raises:
            InterruptedError: If interrupted
        """
        raise NotImplementedError

    def get_fits_headers(self, namespaces: list[str] | None = None) -> dict[str, Any]:
        """Returns FITS header for the current status of this module.

        Args:
            namespaces: If given, only return FITS headers for the given namespaces.

        Returns:
            Dictionary containing FITS headers.
        """
        return {}


__all__ = ["Script"]
