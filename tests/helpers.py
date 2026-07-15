"""Shared test-double helpers used across multiple test modules."""

from __future__ import annotations

import itertools
from unittest.mock import AsyncMock, MagicMock

_mock_class_counter = itertools.count()


def isinstance_class(name: str, interfaces: list[type]) -> type:
    """Build a fresh class purely for isinstance() checks against a MagicMock.

    Uniquely named per call: an unqualified name built only from interface
    bases would otherwise land in the Interface registry (it's structurally
    indistinguishable from a real composite interface) and collide with
    itself across repeated calls, since each call creates a new class object.
    """
    return type(f"_Mock{name}{next(_mock_class_counter)}", tuple(interfaces), {})


def make_proxy_cm(value: object) -> MagicMock:
    """Wrap value in a MagicMock standing in for the async context manager
    returned by Comm.proxy(...)/Comm.safe_proxy(...)."""
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=value)
    cm.__aexit__ = AsyncMock(return_value=None)
    return cm
