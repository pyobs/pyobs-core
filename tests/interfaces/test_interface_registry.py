"""Tests for the import-time interface registry in pyobs/interfaces/interface.py.

Covers registration on subclassing, the "pure interface" bases filter (and its
propagation to further subclasses), lookup helpers, and collision handling.
"""

from __future__ import annotations

from abc import ABCMeta

import pytest

from pyobs.interfaces import Interface
from pyobs.interfaces.interface import get_registered_interface, registered_interfaces

# ── registration on subclassing ─────────────────────────────────────────────


def test_subclass_gets_registered() -> None:
    class IRegistryTestFoo(Interface, metaclass=ABCMeta):
        pass

    assert get_registered_interface("IRegistryTestFoo") is IRegistryTestFoo


def test_registered_interfaces_includes_new_interface() -> None:
    class IRegistryTestBar(Interface, metaclass=ABCMeta):
        pass

    assert registered_interfaces()["IRegistryTestBar"] is IRegistryTestBar


def test_registered_interfaces_returns_snapshot_copy() -> None:
    """Mutating the returned dict must not affect the live registry."""
    snapshot = registered_interfaces()
    snapshot["totally-fake-entry"] = object()  # type: ignore[assignment]

    assert "totally-fake-entry" not in registered_interfaces()


def test_unknown_name_returns_none() -> None:
    assert get_registered_interface("INoSuchRegistryTestInterface") is None


def test_composite_interface_registers() -> None:
    """An interface composing other interfaces (like ICamera(IData, IExposure)) registers too."""

    class IRegistryTestBase(Interface, metaclass=ABCMeta):
        pass

    class IRegistryTestComposite(IRegistryTestBase, metaclass=ABCMeta):
        pass

    assert get_registered_interface("IRegistryTestComposite") is IRegistryTestComposite


# ── pure-interface bases filter ─────────────────────────────────────────────


def test_non_interface_mixin_excluded() -> None:
    """A class mixing in a non-Interface base (like BaseCamera(Module, ICamera, ...))
    must not register itself as an interface."""

    class NotAnInterface:
        pass

    class IRegistryTestPure(Interface, metaclass=ABCMeta):
        pass

    class ImpureMix(NotAnInterface, IRegistryTestPure, metaclass=ABCMeta):
        pass

    assert get_registered_interface("ImpureMix") is None


def test_impurity_propagates_to_subclasses() -> None:
    """Regression test: subclassing an already-impure class must not register either,
    even though its own direct bases look structurally pure (all are Interface
    subclasses). This is the exact shape of the bug that broke DummyCamera(BaseCamera,
    ...): BaseCamera(Module, ICamera, ...) is impure and correctly excluded, but a naive
    `issubclass(base, Interface)` check on DummyCamera's bases would pass, since
    BaseCamera itself transitively satisfies issubclass(BaseCamera, Interface).
    """

    class NotAnInterface:
        pass

    class IRegistryTestPure2(Interface, metaclass=ABCMeta):
        pass

    class ImpureBase(NotAnInterface, IRegistryTestPure2, metaclass=ABCMeta):
        pass

    assert get_registered_interface("ImpureBase") is None

    class ImpureChild(ImpureBase, metaclass=ABCMeta):
        pass

    assert get_registered_interface("ImpureChild") is None


# ── re-import / collision handling ──────────────────────────────────────────


def test_reregistering_same_class_object_is_noop() -> None:
    """Re-importing the same interface module twice resolves to the same class object
    -- must not raise, and the registry entry must be unaffected."""

    class IRegistryTestReimport(Interface, metaclass=ABCMeta):
        pass

    # simulate a second "import" of the same class object landing back in __init_subclass__
    IRegistryTestReimport.__init_subclass__()

    assert get_registered_interface("IRegistryTestReimport") is IRegistryTestReimport


def test_distinct_classes_same_name_collide() -> None:
    """Two genuinely different classes claiming the same name must raise TypeError
    immediately, naming both offending classes."""

    first = type("IRegistryTestDup", (Interface,), {"__module__": "tests.fake_module_a"})
    assert get_registered_interface("IRegistryTestDup") is first

    with pytest.raises(TypeError, match="IRegistryTestDup"):
        type("IRegistryTestDup", (Interface,), {"__module__": "tests.fake_module_b"})

    # the original registration is untouched by the failed second attempt
    assert get_registered_interface("IRegistryTestDup") is first


def test_collision_error_names_both_offending_classes() -> None:
    first = type("IRegistryTestDup2", (Interface,), {"__module__": "tests.fake_module_a"})

    with pytest.raises(TypeError) as exc_info:
        type("IRegistryTestDup2", (Interface,), {"__module__": "tests.fake_module_b"})

    message = str(exc_info.value)
    assert "tests.fake_module_a" in message
    assert "tests.fake_module_b" in message
    assert first.__name__ in message
