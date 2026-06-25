from __future__ import annotations

from collections.abc import Callable, Coroutine
from typing import Any

from pyobs.comm import Comm
from pyobs.events import Event
from pyobs.interfaces import Interface
from pyobs.utils.enums import ModuleState
from pyobs.utils.types import cast_response_to_real

from .localnetwork import LocalNetwork


class LocalComm(Comm):
    def __init__(self, name: str, *args: Any, **kwargs: Any):
        Comm.__init__(self, *args, **kwargs)

        self._name = name
        self._network = LocalNetwork()
        self._network.connect_client(self)

        # in-memory state and capabilities storage
        self._states: dict[str, Any] = {}  # node -> state object
        self._state_handlers: dict[str, list[tuple[type[Interface], Callable[[Any], None]]]] = {}
        self._capabilities: dict[type[Interface], Any] = {}  # interface -> Capabilities object
        self._presence: tuple[ModuleState, str] = (ModuleState.READY, "")

    @property
    def name(self) -> str:
        """Name of this client."""
        return self._name

    @property
    def clients(self) -> list[str]:
        """Returns list of currently connected clients."""
        return self._network.get_client_names()

    async def get_interfaces(self, client: str) -> list[type[Interface]]:
        """Returns list of interfaces for given client."""
        remote_client = self._network.get_client(client)
        return [] if not remote_client.has_module else remote_client.module.interfaces

    async def _supports_interface(self, client: str, interface: type[Interface]) -> bool:
        """Checks whether the given client supports the given interface."""
        interfaces = await self.get_interfaces(client)
        return interface in interfaces

    async def execute(self, client: str, method: str, annotation: dict[str, Any], *args: Any) -> Any:
        """Execute a given method on a remote client."""
        remote_client = self._network.get_client(client)
        if remote_client.module is None:
            raise ValueError
        simple_results = await remote_client.module.execute(method, *args, sender=self.name)
        real_results = cast_response_to_real(
            simple_results, annotation["return"], self.cast_to_real_pre, self.cast_to_real_post
        )
        return real_results

    async def send_event(self, event: Event) -> None:
        """Send an event to other clients."""
        remote_clients = self._network.get_clients()
        for client in remote_clients:
            client._send_event_to_module(event, self.name)

    async def _register_events(
        self, events: list[type[Event]], handler: Callable[[Event, str], Coroutine[Any, Any, bool]] | None = None
    ) -> None:
        pass

    # -------------------------------------------------------------------------
    # State
    # -------------------------------------------------------------------------

    async def _set_state(self, interface: type[Interface], state: Any) -> None:
        """Publish state locally and dispatch to subscribers."""
        node = f"pyobs:state:{self._name}:{interface.__name__}:{interface.version}"
        self._states[node] = state

        # dispatch to all subscribers for this node
        if node in self._state_handlers:
            for _, callback in self._state_handlers[node]:
                callback(state)

    async def _subscribe_state(self, module: str, interface: type[Interface], callback: Callable[[Any], None]) -> None:
        """Subscribe to state updates from a remote module."""
        node = f"pyobs:state:{module}:{interface.__name__}:{interface.version}"

        if node not in self._state_handlers:
            self._state_handlers[node] = []
        self._state_handlers[node].append((interface, callback))

        # also register on the remote comm so it can dispatch to us
        try:
            remote = self._network.get_client(module)
            if node not in remote._state_handlers:
                remote._state_handlers[node] = []
            remote._state_handlers[node].append((interface, callback))

            # deliver current value immediately if available
            if node in remote._states:
                callback(remote._states[node])
        except KeyError:
            pass  # remote not connected yet

    # -------------------------------------------------------------------------
    # Capabilities
    # -------------------------------------------------------------------------

    async def _set_capabilities(self, interface: type[Interface], capabilities: Any) -> None:
        """Store capabilities locally."""
        self._capabilities[interface] = capabilities

    async def _get_capabilities(self, module: str, interface: type[Interface]) -> Any | None:
        """Fetch capabilities from a remote module."""
        if not hasattr(interface, "Capabilities"):
            return None
        try:
            remote = self._network.get_client(module)
            return remote._capabilities.get(interface)
        except KeyError:
            return None

    # -------------------------------------------------------------------------
    # Presence
    # -------------------------------------------------------------------------

    async def _set_presence(self, state: ModuleState, error_string: str = "") -> None:
        """Store presence state locally."""
        self._presence = (state, error_string)

    def _get_client_state(self, module: str) -> tuple[ModuleState, str] | None:
        """Return presence state of a connected module."""
        try:
            remote = self._network.get_client(module)
            return remote._presence
        except KeyError:
            return None
