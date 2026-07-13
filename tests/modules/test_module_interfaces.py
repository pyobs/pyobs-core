"""Tests for Module._get_interfaces_and_methods -- the chokepoint that discovers which
registered interfaces a module implements. Shared by every comm backend (LocalComm reads
Module.interfaces directly; XmppComm publishes it via disco#info), so this is what
actually gates whether an externally-defined interface is ever advertised at all.
"""

from __future__ import annotations

from abc import ABCMeta

from pyobs.interfaces import Interface
from pyobs.interfaces.interface import get_registered_interface
from pyobs.modules import Module


def test_module_discovers_external_interface() -> None:
    """A module implementing an interface defined entirely outside pyobs.interfaces
    still has it show up in .interfaces -- this is what makes external-package
    interfaces publishable in the first place."""

    class IModuleTestExternal(Interface, metaclass=ABCMeta):
        async def do_the_thing(self) -> None: ...

    class ModuleTestImpl(Module, IModuleTestExternal):
        async def do_the_thing(self) -> None:
            pass

    m = ModuleTestImpl()

    assert IModuleTestExternal in m.interfaces


def test_module_class_itself_not_registered_as_interface() -> None:
    """Regression test: a concrete module implementation must not itself land in the
    interface registry (it would otherwise appear in its own .interfaces list)."""

    class IModuleTestExternal2(Interface, metaclass=ABCMeta):
        pass

    class ModuleTestImpl2(Module, IModuleTestExternal2):
        pass

    m = ModuleTestImpl2()

    assert ModuleTestImpl2 not in m.interfaces
    assert get_registered_interface("ModuleTestImpl2") is None


def test_module_collects_methods_for_external_interface() -> None:
    class IModuleTestWithMethod(Interface, metaclass=ABCMeta):
        async def custom_method(self, value: int) -> int: ...

    class ModuleTestMethodImpl(Module, IModuleTestWithMethod):
        async def custom_method(self, value: int) -> int:
            return value * 2

    m = ModuleTestMethodImpl()

    assert "custom_method" in m.methods
    assert "custom_method" in m._interface_methods["IModuleTestWithMethod"]


def test_module_still_discovers_core_interfaces() -> None:
    """Sanity check that the registry-driven rewrite didn't break core interface
    discovery -- every Module implements IModule and IConfig."""
    from pyobs.interfaces import IConfig, IModule

    m = Module()

    assert IModule in m.interfaces
    assert IConfig in m.interfaces
