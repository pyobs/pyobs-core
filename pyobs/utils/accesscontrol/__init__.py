from pyobs.object import Object


class AccessControl(Object):
    """Base class for accesscontrol."""

    def has_access(self, client: str, module: str, method: str) -> bool:
        """Check if a client has access to a method.

        This method *must* be implemented by subclasses, since this implementation always returns True.

        Args:
            client: Name of client.
            module: Name of module.
            method: Name of method.

        Returns:
            Whether the given client is allowed to call the given method on the current module.
        """
        return True
