"""Struct field schemas in disco#info's <types> block (pyobs-core#898).

`_wire_type()` already publishes an enum's possible values in <types> so a schema-driven
client can build a <select> with no hardcoded per-interface knowledge. These tests cover
the equivalent treatment for dataclass ("struct<Name>") fields: field name/type/unit
publication, one level of struct-in-struct nesting, the depth cap that keeps deeper
nesting (and self-/mutually-recursive dataclasses) from looping, and enums nested inside
a struct still registering in the shared <types> block.

Pure unit tests: no XMPP connection, no live ejabberd.
"""

from __future__ import annotations

import dataclasses
from abc import ABCMeta, abstractmethod
from enum import StrEnum
from typing import Annotated, Any

from pyobs.comm.xmpp.serializer import StructFields, _interface_schema_to_xml, _wire_type
from pyobs.interfaces.interface import Interface
from pyobs.utils.enums import Unit


@dataclasses.dataclass
class _FlatStruct:
    name: str
    value: Annotated[float, Unit.DEGREES]
    note: str | None = None


@dataclasses.dataclass
class _InnerStruct:
    x: int


@dataclasses.dataclass
class _OuterStruct:
    inner: _InnerStruct
    label: str


@dataclasses.dataclass
class _Level2:
    v: int


@dataclasses.dataclass
class _Level1:
    l2: _Level2


@dataclasses.dataclass
class _Level0:
    l1: _Level1


@dataclasses.dataclass
class _SelfRef:
    child: _SelfRef | None = None


@dataclasses.dataclass
class _MutualA:
    b: _MutualB


@dataclasses.dataclass
class _MutualB:
    a: _MutualA


class _Color(StrEnum):
    RED = "red"
    BLUE = "blue"


@dataclasses.dataclass
class _ColoredStruct:
    color: _Color


def test_flat_struct_fields_are_published() -> None:
    structs: dict[str, StructFields] = {}
    type_str, _ = _wire_type(_FlatStruct, {}, structs)

    assert type_str == "struct<_FlatStruct>"
    assert structs["_FlatStruct"] == [
        ("name", "string", None),
        ("value", "float64", "deg"),
        ("note", "optional<string>", None),
    ]


def test_one_level_of_struct_nesting_is_walked() -> None:
    structs: dict[str, StructFields] = {}
    _wire_type(_OuterStruct, {}, structs)

    assert structs["_OuterStruct"] == [("inner", "struct<_InnerStruct>", None), ("label", "string", None)]
    assert structs["_InnerStruct"] == [("x", "int32", None)]


def test_struct_nesting_beyond_one_level_is_not_expanded() -> None:
    structs: dict[str, StructFields] = {}
    _wire_type(_Level0, {}, structs)

    assert "_Level0" in structs
    assert "_Level1" in structs
    # _Level1's own field is still a struct<_Level2> reference, but _Level2 itself never
    # gets a fields entry -- it's two levels below the top-level struct.
    assert structs["_Level1"] == [("l2", "struct<_Level2>", None)]
    assert "_Level2" not in structs


def test_self_referential_struct_terminates() -> None:
    structs: dict[str, StructFields] = {}
    _wire_type(_SelfRef, {}, structs)

    assert structs["_SelfRef"] == [("child", "optional<struct<_SelfRef>>", None)]


def test_mutually_recursive_structs_terminate() -> None:
    structs: dict[str, StructFields] = {}
    _wire_type(_MutualA, {}, structs)

    assert structs["_MutualA"] == [("b", "struct<_MutualB>", None)]
    assert structs["_MutualB"] == [("a", "struct<_MutualA>", None)]


def test_enum_nested_in_struct_is_registered_in_both() -> None:
    enums: dict[str, type] = {}
    structs: dict[str, StructFields] = {}
    _wire_type(_ColoredStruct, enums, structs)

    assert structs["_ColoredStruct"] == [("color", "enum(_Color)", None)]
    assert enums["_Color"] is _Color


class _TestStructInterface(Interface, metaclass=ABCMeta):
    """Test-only interface with a struct-typed command param."""

    @abstractmethod
    async def do_thing(self, elements: _FlatStruct, **kwargs: Any) -> None: ...


def test_interface_schema_publishes_struct_in_types_block() -> None:
    root = _interface_schema_to_xml(_TestStructInterface)

    types_elem = root.find("types")
    assert types_elem is not None
    struct_elem = types_elem.find("struct[@name='_FlatStruct']")
    assert struct_elem is not None

    fields = {f.get("name"): (f.get("type"), f.get("unit")) for f in struct_elem.findall("field")}
    assert fields == {
        "name": ("string", None),
        "value": ("float64", "deg"),
        "note": ("optional<string>", None),
    }

    param_elem = root.find("command[@name='do_thing']/parameter[@name='elements']")
    assert param_elem is not None
    assert param_elem.get("type") == "struct<_FlatStruct>"


class _TestEnumOnlyInterface(Interface, metaclass=ABCMeta):
    """Test-only interface with only an enum param -- no <struct> noise expected."""

    @abstractmethod
    async def set_color(self, color: _Color, **kwargs: Any) -> None: ...


def test_types_block_has_no_struct_element_when_no_structs_present() -> None:
    root = _interface_schema_to_xml(_TestEnumOnlyInterface)

    types_elem = root.find("types")
    assert types_elem is not None
    assert types_elem.find("enum[@name='_Color']") is not None
    assert types_elem.find("struct") is None


class _TestPlainInterface(Interface, metaclass=ABCMeta):
    """Test-only interface with no enum/struct params -- no <types> block at all."""

    @abstractmethod
    async def do_nothing(self, **kwargs: Any) -> None: ...


def test_no_types_block_when_no_enums_or_structs() -> None:
    root = _interface_schema_to_xml(_TestPlainInterface)
    assert root.find("types") is None
