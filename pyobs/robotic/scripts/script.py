from __future__ import annotations
import logging
from typing import Any, TypeVar, TYPE_CHECKING

from pyobs.utils.serialization import SubClassBaseModel

if TYPE_CHECKING:
    from pyobs.robotic.task import TaskData
    from pyobs.comm import Comm

log = logging.getLogger(__name__)


ProxyClass = TypeVar("ProxyClass")


class Script(SubClassBaseModel):

    async def can_run(self, data: TaskData) -> bool:
        """Checks whether this script could run now.

        Returns:
            True, if the script can run now.
        """
        return True

    async def run(self, data: TaskData) -> None:
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

    @staticmethod
    def __comm(data: TaskData) -> Comm:
        if data.comm is None:
            raise ValueError("No communication module found")
        return data.comm


__all__ = ["Script"]
