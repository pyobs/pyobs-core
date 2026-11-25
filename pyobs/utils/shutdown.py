"""Lets a module ask whoever stops it for more time to shut down.

A module with a long shutdown (e.g. a cooled camera warming up in ``close()``) calls
:func:`extend_stop_timeout`. Depending on how the module was started, that

- sends ``EXTEND_TIMEOUT_USEC`` to systemd, if ``$NOTIFY_SOCKET`` is set (see ``sd_notify(3)``; systemd
  only honors it for ``Type=notify`` services), and/or
- writes the deadline (wall-clock epoch seconds) into a stop file next to the PID file, if the module was
  started with ``--pid-file`` (pyobsd's and web-admin's PID-file mode). They read it with
  :func:`read_stop_deadline` and only send SIGKILL after that deadline.

Without either, it does nothing.
"""

from __future__ import annotations

import logging
import os
import socket
import time

log = logging.getLogger(__name__)

STOP_FILE_SUFFIX = ".stopping"

_stop_file: str | None = None


def stop_file_for(pid_file: str) -> str:
    """Path of the stop file belonging to a PID file."""
    return pid_file + STOP_FILE_SUFFIX


def set_stop_file(path: str | None) -> None:
    """Sets the stop file that :func:`extend_stop_timeout` writes to. Called by the application."""
    global _stop_file
    _stop_file = path


def extend_stop_timeout(seconds: float) -> None:
    """Asks for up to ``seconds`` more time to shut down, counted from now. Never raises."""
    notify(f"EXTEND_TIMEOUT_USEC={int(seconds * 1_000_000)}")
    if _stop_file is not None:
        _write_deadline(_stop_file, time.time() + seconds)


def clear_stop_file() -> None:
    """Removes the stop file, if any. Called by the application at the end of its shutdown."""
    if _stop_file is None:
        return
    try:
        os.remove(_stop_file)
    except FileNotFoundError:
        pass
    except OSError as e:
        log.warning("Could not remove stop file %s: %s", _stop_file, e)


def read_stop_deadline(path: str) -> float | None:
    """Reads the deadline (epoch seconds) from a stop file, or None if there is no valid one."""
    try:
        with open(path) as f:
            return float(f.read().strip())
    except (OSError, ValueError):
        return None


def notify(message: str) -> bool:
    """Sends one message to systemd's notification socket, without libsystemd.

    Returns:
        True if it was sent, False if ``$NOTIFY_SOCKET`` is not set or sending failed.
    """
    address = os.environ.get("NOTIFY_SOCKET")
    if not address:
        return False
    if address[0] == "@":
        # abstract namespace
        address = "\0" + address[1:]
    elif address[0] != "/":
        log.warning("Unsupported NOTIFY_SOCKET %r, not notifying systemd.", address)
        return False
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM | socket.SOCK_CLOEXEC) as sock:
            sock.connect(address)
            sock.sendall(message.encode())
        return True
    except OSError as e:
        log.warning("Could not notify systemd (%s): %s", message, e)
        return False


def _write_deadline(path: str, deadline: float) -> None:
    tmp = f"{path}.{os.getpid()}.tmp"
    try:
        with open(tmp, "w") as f:
            f.write(f"{deadline:.3f}\n")
        os.replace(tmp, path)
    except OSError as e:
        log.warning("Could not write stop file %s: %s", path, e)


__all__ = [
    "STOP_FILE_SUFFIX",
    "stop_file_for",
    "set_stop_file",
    "extend_stop_timeout",
    "clear_stop_file",
    "read_stop_deadline",
    "notify",
]
