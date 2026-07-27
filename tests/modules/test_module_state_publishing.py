"""Parametrized check: every concrete Module publishes state for each stateful interface it
implements by the end of open() -- see specs/plans/enforce-state-publishing.md.

Discovers all concrete pyobs.modules.Module subclasses, instantiates each with a DummyComm
(the default when no comm is given), runs open(), and asserts Comm.missing_published_state()
is empty. Modules that can't be constructed/opened without real external config or hardware
are skipped rather than failed -- this test is a development aid, not exhaustive coverage.
"""

from __future__ import annotations

import asyncio
import importlib
import inspect
import pkgutil
from typing import Any

import astropy.units as u
import pytest
from astroplan import Observer

import pyobs.modules as modules_pkg
from pyobs.modules import Module

pytest_plugins = ("pytest_asyncio",)

_OPEN_TIMEOUT_SECONDS = 5.0

_OBSERVER = Observer(latitude=52.0 * u.deg, longitude=10.0 * u.deg, elevation=100.0 * u.m)

# Extra constructor kwargs for modules whose no-arg construction succeeds but whose state
# publish is gated on optional config -- e.g. the dummy telescopes only publish IPointingAltAz
# once an Observer/location is known. Without this, the test would report a false-positive
# "missing state" for an unconfigured optional feature rather than an actual bug.
_EXTRA_KWARGS: dict[str, dict[str, Any]] = {
    "DummyAltAzTelescope": {"observer": _OBSERVER, "location": _OBSERVER.location},
    "DummyRaDecTelescope": {"observer": _OBSERVER, "location": _OBSERVER.location},
    "DummySolarTelescope": {"observer": _OBSERVER, "location": _OBSERVER.location},
    # Weather's constructor only stores the URL (WeatherApi does no I/O until _update() runs,
    # which open() doesn't call) -- a fake URL lets this test actually exercise Weather's
    # open()-time placeholder publish instead of skipping the plan's motivating example.
    "Weather": {"url": "http://weather.example.invalid"},
}


def _discover_concrete_modules() -> list[type[Module]]:
    """All concrete (non-abstract, non-internal) pyobs.modules.Module subclasses.

    Leading-underscore classes (e.g. _DummyTelescopeBase) are excluded: they're internal
    implementation bases, and every one currently in pyobs-core is already exercised via a
    public concrete subclass that inherits its open() unchanged, so including it too would
    just test the same code path twice under a name that isn't part of the module inventory.
    """
    seen: set[type[Module]] = set()
    for _, name, _ in pkgutil.walk_packages(modules_pkg.__path__, modules_pkg.__name__ + "."):
        try:
            mod = importlib.import_module(name)
        except ImportError:
            continue
        for obj in vars(mod).values():
            if (
                inspect.isclass(obj)
                and issubclass(obj, Module)
                and obj is not Module
                and not inspect.isabstract(obj)
                and not obj.__name__.startswith("_")
            ):
                seen.add(obj)
    return sorted(seen, key=lambda c: f"{c.__module__}.{c.__name__}")


_MODULES = _discover_concrete_modules()


@pytest.mark.asyncio
@pytest.mark.parametrize("cls", _MODULES, ids=lambda c: f"{c.__module__}.{c.__name__}")
async def test_module_publishes_all_stateful_interfaces(cls: type[Module]) -> None:
    kwargs = _EXTRA_KWARGS.get(cls.__name__, {})

    try:
        module = cls(**kwargs)
    except Exception as e:
        pytest.skip(f"cannot construct without external config: {e!r}")

    try:
        await asyncio.wait_for(module.open(), timeout=_OPEN_TIMEOUT_SECONDS)
    except Exception as e:
        pytest.skip(f"cannot open without external config/hardware: {e!r}")

    try:
        missing = module.comm.missing_published_state(module.interfaces)
        assert missing == [], (
            f"{cls.__module__}.{cls.__name__} implements {[i.__name__ for i in missing]}, "
            "which declare state, but open() never published it"
        )
    finally:
        try:
            await asyncio.wait_for(module.close(), timeout=_OPEN_TIMEOUT_SECONDS)
        except Exception:
            pass
