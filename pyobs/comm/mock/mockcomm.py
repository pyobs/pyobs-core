from __future__ import annotations
from typing import Any, Type

from pyobs.comm import Comm
from pyobs.interfaces import Interface
import pyobs.interfaces


class MockModule:
    def __init__(self, name: str, interfaces: list[str], methods: dict[str, str | dict[str, str]]):
        self.name = name
        self.interfaces = [getattr(pyobs.interfaces, i) for i in interfaces]
        self.methods = methods

    def execute(self, method: str, *args: Any) -> Any:
        if method in self.methods:
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
        return self.modules[client].execute(method, *args)


__all__ = ["MockComm"]
