from __future__ import annotations
import logging
from typing import Any, Type

from pyobs.comm import Comm
from pyobs.comm.comm import ProxyType
from pyobs.interfaces import Interface
import pyobs.interfaces


log = logging.getLogger(__name__)


class MockModule:
    def __init__(self, name: str, interfaces: list[str], methods: dict[str, str | dict[str, str]] | None = None):
        self.name = name
        self.interfaces = [getattr(pyobs.interfaces, i) for i in interfaces]
        self.methods = methods

    def execute(self, method: str, *args: Any) -> Any:
        if self.methods is not None and method in self.methods:
            return self.methods[method]
        else:
            return None


class MockComm(Comm):
    """A mock class for pyobs comm."""

    __module__ = "pyobs.comm.mock"

    def __init__(
        self,
        mock: dict[str, Any],
        *args: Any,
        **kwargs: Any,
    ):
        """Create a new mock Comm module.

        Args:
        """
        Comm.__init__(self, *args, **kwargs)
        self.modules = {name: MockModule(name, **config) for name, config in mock.items()}

    @property
    def name(self) -> str | None:
        """Name of this client."""
        return "mock"

    async def proxy(self, name_or_object: str | object, obj_type: Type[ProxyType] | None = None) -> Any | ProxyType:
        if isinstance(name_or_object, str) and name_or_object not in self.modules:
            log.warning(f"Calling module {name_or_object} that is not mocked.")
        return await super().proxy(name_or_object, obj_type)

    async def get_interfaces(self, client: str) -> list[Type[Interface]]:
        """Returns list of interfaces for given client.

        Args:
            client: Name of client.

        Returns:
            List of supported interfaces.

        Raises:
            IndexError: If client cannot be found.
        """
        return self.modules[client].interfaces

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
        log.info(f"Calling {client}.{method}...")
        return self.modules[client].execute(method, *args)


__all__ = ["MockComm"]
