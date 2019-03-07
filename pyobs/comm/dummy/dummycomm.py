import logging
from typing import Any

from pyobs.comm import Comm


log = logging.getLogger(__name__)


class DummyComm(Comm):
    """A dummy implementation of the Comm interface."""

    def __init__(self, *args, **kwargs):
        """Creates a new dummy comm."""
        Comm.__init__(self, *args, **kwargs)

    @property
    def clients(self):
        """Always return zero clients."""
        return []

    def _get_interfaces(self, item):
        """No interfaces implemented."""
        return []

    def _supports_interface(self, client, interface):
        """Interfaces are never supported."""
        return False

    def add_command_handler(self, command, handler):
        """Always accept adding new command handlers."""
        return True

    def del_command_handler(self, command, handler):
        """Always accept deleting command handlers."""
        return True

    def send_text_message(self, client, msg):
        """Always allow sending text message."""
        return True

    def execute(self, client: str, method: str, *args) -> Any:
        """Always fake a successful execution of a method."""
        return True


__all__ = ['DummyComm']
