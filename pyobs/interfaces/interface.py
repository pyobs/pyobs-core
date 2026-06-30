from abc import ABCMeta
from typing import Any, ClassVar


class Interface(metaclass=ABCMeta):
    """Base class for all interfaces in pyobs."""

    version: int = 1
    state: ClassVar[type | None] = None
    capabilities: ClassVar[type | None] = None

    __module__ = "pyobs.interfaces"

    def get_state(self, interface: "type[Interface]") -> Any | None:
        """Return the last received state for the given interface, or None."""
        return None

    def get_capabilities(self, interface: "type[Interface]") -> Any | None:
        """Return the capabilities for the given interface, or None."""
        return None


__all__ = ["Interface"]
