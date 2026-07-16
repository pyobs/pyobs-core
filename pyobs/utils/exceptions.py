from __future__ import annotations

import logging
from collections.abc import Callable, Coroutine
from typing import Any, NamedTuple

"""
TODO: Write docs
"""
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


class UnclassifiedError(PyobsError):
    """Wraps an exception that isn't part of the deliberate PyobsError contract -- either it never
    was a PyobsError to begin with (a builtin, a vendor SDK exception) and escaped a module's own
    method body unconverted, or it crossed an RPC boundary and couldn't be reconstructed as its real
    type because its defining module was never imported in this process. The original type name
    survives as `original_type` even when the class itself doesn't."""

    pass


#######################################

# The hierarchy above this point is domain-level: each type means "the operation failed for
# reason X," and per goal 5, domain exceptions deliberately multiply into fine-grained leaves so a
# caller can react differently to each one. RemoteError and its subtree below are the other axis
# entirely -- they mean "the call itself didn't reach/return" (a transport failure), not "the
# remote operation failed for a domain reason." That distinction doesn't benefit from the same
# fine-grained treatment: "the call failed to even happen" doesn't usually need to distinguish
# *why* the way a domain failure does, so RemoteError's own subtree stays deliberately small.
# A domain exception raised on the far side of an RPC call no longer travels through this
# subtree at all (see rpc.py's fault reconstruction) -- it arrives as its own real type directly,
# tagged with `remote_module`, not wrapped in a RemoteError.


class RemoteError(PyobsError):
    """Exception for anything related to the communication between modules."""

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
