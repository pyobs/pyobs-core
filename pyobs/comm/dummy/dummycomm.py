from __future__ import annotations

import logging
from typing import Any

from pyobs.comm import Comm
from pyobs.events import Event
from pyobs.interfaces import Interface
from pyobs.utils.parallel import Future

log = logging.getLogger(__name__)


class DummyComm(Comm):
    """A dummy implementation of the Comm interface."""

    def __init__(self, name: str = "module", *args: Any, **kwargs: Any):
        """Creates a new dummy comm.

        Args:
            name: Name to report for this comm. Defaults to the generic placeholder "module"
                for callers (e.g. tests) that construct a DummyComm directly without a real
                identity; Application fills in the config file's stem when a module has no
                comm of its own configured.
        """
        Comm.__init__(self, *args, **kwargs)
        self._name = name

    @property
    def clients(self) -> list[str]:
        """Always return zero clients."""
        return []

    async def get_interfaces(self, client: str) -> list[type[Interface]]:
        """No interfaces implemented."""
        return []

    async def _supports_interface(self, client: str, interface: type[Interface]) -> bool:
        """Interfaces are never supported."""
        return False

    async def execute(self, client: str, method: str, annotation: dict[str, Any], *args: Any) -> Any:
        """Execute a given method on a remote client.

        Args:
            client (str): ID of client.
            method (str): Method to call.
            annotation: Method annotation.
            *args: List of parameters for given method.

        Returns:
            Passes through return from method call.
        """
        return Future(empty=True)

    @property
    def name(self) -> str:
        """Name of this client."""
        return self._name

    async def send_event(self, event: Event) -> None:
        """Send an event to other clients.

        Args:
            event (Event): Event to send
        """
        self._send_event_to_module(event, self._name)


__all__ = ["DummyComm"]
