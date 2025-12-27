from abc import ABCMeta, abstractmethod

from pyobs.object import Object


class AccessControl(Object, metaclass=ABCMeta):
    """Abstract base class for accesscontrol."""

    @abstractmethod
    def has_access(self, client: str, module: str, method: str) -> bool:
        """Check if a client has access to a method.

        This method *must* be implemented by subclasses!

        Args:
            client: Name of client.
            module: Name of module.
            method: Name of method.

        Returns:
            Whether the given client is allowed to call the given method on the current module.
        """
        ...
