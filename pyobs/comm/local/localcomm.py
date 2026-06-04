from typing import Any
from collections.abc import Callable, Coroutine

from pyobs.comm import Comm
from pyobs.events import Event
from pyobs.interfaces import Interface
from pyobs.utils.types import cast_response_to_real
from .localnetwork import LocalNetwork


class LocalComm(Comm):
    def __init__(self, name: str, *args: Any, **kwargs: Any):
        Comm.__init__(self, *args, **kwargs)

        self._name = name
        self._network = LocalNetwork()
        self._network.connect_client(self)

    @property
    def name(self) -> str:
        """Name of this client."""
        return self._name

    @property
    def clients(self) -> list[str]:
        """Returns list of currently connected clients.

        Returns:
            (list) List of currently connected clients.
        """
        return self._network.get_client_names()

    async def get_interfaces(self, client: str) -> list[type[Interface]]:
        """Returns list of interfaces for given client.

        Args:
            client: Name of client.

        Returns:
            List of supported interfaces.

        Raises:
            IndexError: If client cannot be found.
        """

        remote_client: LocalComm = self._network.get_client(client)
        return [] if remote_client.module is None else remote_client.module.interfaces

    async def _supports_interface(self, client: str, interface: type[Interface]) -> bool:
        """Checks, whether the given client supports the given interface.

        Args:
            client: Client to check.
            interface: Interface to check.

        Returns:
            Whether interface is supported.
        """
        interfaces = await self.get_interfaces(client)
        return interface in interfaces

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

        remote_client = self._network.get_client(client)
        if remote_client.module is None:
            raise ValueError
        simple_results = await remote_client.module.execute(method, *args, sender=self.name)
        real_results = cast_response_to_real(
            simple_results, annotation["return"], self.cast_to_real_pre, self.cast_to_real_post
        )
        return real_results

    async def send_event(self, event: Event) -> None:
        """Send an event to other clients.

        Args:
            event (Event): Event to send
        """

        remote_clients = self._network.get_clients()
        for client in remote_clients:
            client._send_event_to_module(event, self.name)

    async def _register_events(
        self, events: list[type[Event]], handler: Callable[[Event, str], Coroutine[Any, Any, bool]] | None = None
    ) -> None:
        pass
