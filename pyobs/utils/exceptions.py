"""The pyobs exception hierarchy, used both for local errors and to carry failures across the RPC
boundary between modules.

Two independent axes live in this hierarchy:

- **Domain exceptions** (everything above `RemoteError` below) mean "the operation failed for
  reason X." These deliberately multiply into fine-grained leaves (`MoveError`, `FocusError`,
  `GrabImageError`, ...) so a caller can react differently to each one, rather than catching one
  broad type and inspecting a message string.
- **`RemoteError`** and its small subtree mean "the call itself didn't reach/return" (a transport
  failure), not "the remote operation failed for a domain reason." That distinction doesn't
  benefit from the same fine-grained treatment, so it stays deliberately small.

A domain exception raised on the far side of an RPC call is looked up in the registry below by its
fully-qualified name and re-raised locally as its real type, tagged with `remote_module` (see
`comm/xmpp/rpc.py`'s fault reconstruction) -- it does not travel wrapped in a `RemoteError`. If the
type can't be resolved (its defining module was never imported in this process, or it was never a
`PyobsError` to begin with), it arrives as `UnclassifiedError` instead, with the original type name
preserved as `original_type`.

Every subclass registers itself automatically via `__init_subclass__` (`PyobsError._registry`);
there's nothing to do at definition time beyond subclassing the right branch of the hierarchy.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Coroutine
from typing import Any, NamedTuple

__title__ = "Exceptions"


class PyobsError(Exception):
    """Base class for all exceptions"""

    _registry: dict[str, type[PyobsError]] = {}

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        PyobsError._registry[f"{cls.__module__}.{cls.__qualname__}"] = cls

    def __init__(self, message: str | None = None, **context: Any) -> None:
        self.message = message
        self.logged = False
        self.context = context
        for key, value in context.items():
            setattr(self, key, value)

    def __str__(self) -> str:
        msg = f"<{self.__class__.__name__}>"
        if self.message is not None:
            msg += f" {self.message}"
        return msg

    def log(self, log: logging.Logger, level: str, message: str, **kwargs: Any) -> None:
        if self.logged:
            return
        log.log(logging.getLevelName(level), message, **kwargs)
        self.logged = True

    @classmethod
    def resolve(cls, qualified_name: str) -> type[PyobsError] | None:
        return cls._registry.get(qualified_name)


#######################################


class ModuleError(PyobsError):
    pass


class GeneralError(PyobsError):
    pass


class ImageError(PyobsError):
    pass


class MotionError(PyobsError):
    pass


class InitError(MotionError):
    pass


class ParkError(MotionError):
    pass


class MoveError(MotionError):
    pass


class GrabImageError(PyobsError):
    pass


class AbortedError(PyobsError):
    pass


class FocusError(PyobsError):
    pass


class AcquisitionError(PyobsError):
    pass


class DeviceBusyError(PyobsError):
    """The device can't service this request right now because it's already busy with another
    operation (e.g. an exposure/sequence already running, or another motion in progress) -- back
    off and retry, as opposed to GrabImageError/MoveError/etc., which mean the operation was
    actually attempted and failed. Deliberately one type across camera/telescope/roof/focuser
    modules alike, not split by device or by which specific operation was busy -- no caller reacts
    differently to those variants."""

    pass


class NotSupportedError(PyobsError):
    """This module doesn't support the requested operation at all -- a capability the module only
    optionally implements (e.g. an alt/az-only telescope asked to move_radec) isn't available,
    as opposed to a specific attempt at that operation failing. Cross-cutting: any module with an
    optional-capability mixin can raise this, not just telescopes."""

    pass


class InvalidArgumentError(PyobsError):
    """The caller passed an argument this method rejects (unknown name, out-of-range value, ...).
    Unlike a plain ValueError, this survives an RPC round trip as itself, so `except
    exc.InvalidArgumentError:` around a proxy call actually catches it -- a bare ValueError would
    silently degrade to UnclassifiedError the moment the call crosses XMPP, even though it works
    fine locally (LocalComm, direct calls, tests), which is exactly the kind of inconsistency that
    only shows up once code goes from a local test to a networked deployment. Deliberately one
    type across every setter-shaped method, not split per method or per argument -- no caller
    reacts differently to "unknown filter" vs. "invalid focus value."""

    pass


class UnclassifiedError(PyobsError):
    """Wraps an exception that isn't part of the deliberate PyobsError contract -- either it never
    was a PyobsError to begin with (a builtin, a vendor SDK exception) and escaped a module's own
    method body unconverted, or it crossed an RPC boundary and couldn't be reconstructed as its real
    type because its defining module was never imported in this process. The original type name
    survives as `original_type` even when the class itself doesn't."""

    pass


#######################################


class RemoteError(PyobsError):
    """The call itself didn't reach/return -- a transport failure, not a domain exception raised
    by the remote operation (see the module docstring for that distinction). Kept deliberately
    small: "the call failed to even happen" doesn't need the same fine-grained treatment as a
    domain failure."""

    pass


class RemoteTimeoutError(RemoteError):
    pass


class ForbiddenError(RemoteError):
    """Raised when a caller is not permitted to invoke a method under the target module's ACL policy."""

    pass


#######################################


class LoggedException(NamedTuple):
    time: float
    exception: PyobsError


class ExceptionHandler(NamedTuple):
    exc_type: type[PyobsError]
    limit: int
    timespan: float | None = None
    module: str | None = None
    callback: Callable[[PyobsError], Coroutine[Any, Any, None]] | None = None


#######################################
