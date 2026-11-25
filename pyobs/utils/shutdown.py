"""Lets a module ask whoever stops it for more time to shut down.

A module with a long shutdown (e.g. a cooled camera warming up in ``close()``) calls
:func:`extend_stop_timeout`. Depending on how the module was started, that

- sends ``EXTEND_TIMEOUT_USEC`` to systemd, if ``$NOTIFY_SOCKET`` is set (see ``sd_notify(3)``; systemd
  only honors it for ``Type=notify`` services), and/or
- writes the deadline (wall-clock epoch seconds) into a stop file next to the PID file, if the module was
  started with ``--pid-file`` (pyobsd's and web-admin's PID-file mode). They read it with
  :func:`read_stop_deadline` and only send SIGKILL after that deadline.

Without either, it only moves the module's own deadline (see :func:`start_watchdog`).

On the first signal, the application also starts a watchdog thread (:func:`start_watchdog`). It ends the
process with ``os._exit(1)`` if the shutdown runs past the deadline, so a module whose shutdown hangs does not
stay "stopping" forever when nobody is waiting to send SIGKILL (``pyobsd stop --no-wait``, Ctrl+C on
``pyobsd stop``).
"""

from __future__ import annotations

import logging
import os
import socket
import threading
import time

log = logging.getLogger(__name__)

STOP_FILE_SUFFIX = ".stopping"

# seconds the watchdog waits past the deadline before ending the process, so that pyobsd's SIGKILL (at the
# deadline) usually comes first, and the module only ends itself when nobody else does
WATCHDOG_GRACE_SECONDS = 5.0

_stop_file: str | None = None

# the module's own deadline (epoch seconds), as last set by mark_stopping()/extend_stop_timeout()
_deadline: float | None = None
_watchdog: threading.Thread | None = None


def stop_file_for(pid_file: str) -> str:
    """Path of the stop file belonging to a PID file."""
    return pid_file + STOP_FILE_SUFFIX


def set_stop_file(path: str | None) -> None:
    """Sets the stop file that :func:`extend_stop_timeout` writes to. Called by the application."""
    global _stop_file
    _stop_file = path


def mark_stopping() -> None:
    """Marks the module as shutting down, without asking for more time. Called by the application on SIGTERM.

    In PID-file mode, the stop file is what makes pyobsd and web-admin show the module as "stopping". The deadline
    written is "now" (or a later one that is already there), which extends nothing, since they always wait at least
    their own stop timeout. Under systemd, sends ``STOPPING=1``. Never raises."""
    global _deadline
    _deadline = max(time.time(), _deadline or 0.0)
    notify("STOPPING=1")
    if _stop_file is not None:
        _write_deadline(_stop_file, max(time.time(), read_stop_deadline(_stop_file) or 0.0))


def extend_stop_timeout(seconds: float) -> None:
    """Asks for up to ``seconds`` more time to shut down, counted from now. Never raises."""
    global _deadline
    _deadline = time.time() + seconds
    notify(f"EXTEND_TIMEOUT_USEC={int(seconds * 1_000_000)}")
    if _stop_file is not None:
        _write_deadline(_stop_file, time.time() + seconds)


def clear_stop_file() -> None:
    """Removes the stop file, if any, and forgets the deadline. Called by the application at the end of its
    shutdown."""
    global _deadline
    _deadline = None
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


def current_deadline() -> float | None:
    """The module's own deadline (epoch seconds), as last set by :func:`mark_stopping` or
    :func:`extend_stop_timeout`, or None."""
    return _deadline


def start_watchdog(stop_timeout: float, grace: float = WATCHDOG_GRACE_SECONDS, interval: float = 1.0) -> None:
    """Starts a daemon thread that ends the process if its shutdown takes too long. Called by the application
    on the first signal; calling it again does nothing.

    "Too long" is the same as for pyobsd: ``stop_timeout`` after now, or later if the module asked for more
    time via :func:`extend_stop_timeout`, plus ``grace``. The thread checks the deadline every ``interval``
    seconds, so later extensions apply. Being a daemon thread, it also covers a hang after ``run()`` returned,
    e.g. while the interpreter waits for a blocked executor thread."""
    global _watchdog
    if _watchdog is not None:
        return
    default_deadline = time.time() + stop_timeout
    _watchdog = threading.Thread(
        target=_watch, args=(default_deadline, grace, interval), name="pyobs-shutdown-watchdog", daemon=True
    )
    _watchdog.start()


def _watch(default_deadline: float, grace: float, interval: float) -> None:
    last: float | None = None
    while True:
        # keep the last deadline seen, clear_stop_file() resets it at the very end of the shutdown
        last = _deadline if _deadline is not None else last
        deadline = max(default_deadline, last or 0.0) + grace
        now = time.time()
        if now >= deadline:
            break
        time.sleep(min(interval, deadline - now))

    log.error("Shutdown did not finish in time, exiting now.")
    clear_stop_file()
    for handler in logging.getLogger().handlers:
        try:
            handler.flush()
        except Exception:
            pass
    os._exit(1)


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
    "mark_stopping",
    "extend_stop_timeout",
    "clear_stop_file",
    "read_stop_deadline",
    "current_deadline",
    "start_watchdog",
    "notify",
]
