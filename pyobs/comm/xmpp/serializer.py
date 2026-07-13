"""Shared XML serializer for pyobs 2.0 (urn:pyobs:rpc:1).

Both the state pub/sub path and the RPC path use the same vocabulary for
individual values. This module provides the canonical implementation.

Wire vocabulary
---------------
Inside any container element (e.g. <pyobs:value> for RPC, a named field
element for State), scalar values are represented as:

    <boolean>true|false</boolean>
    <int>42</int>
    <double>3.14</double>
    <string>text</string>

Composite values:
    <items><item>...</item>...</items>         list
    <tuple><item>...</item>...</tuple>         tuple
    <dict><entry><key>...</key><val>...</val></entry>...</dict>  dict
    <{ns}state><field>...</field>...</{ns}state>  dataclass

The tag names are plain (no namespace) when serialized. After an ejabberd
round-trip they may arrive with a parent namespace prefix — callers should
strip the namespace from the tag before matching (tag.split('}')[-1]).
"""

from __future__ import annotations

import dataclasses
import inspect
import types as _builtin_types
from enum import StrEnum
from typing import Annotated, Any, Union, get_args, get_origin, get_type_hints

import numpy as np
from slixmpp.xmlstream import ET

from ...interfaces.interface import Interface as _Interface
from ...utils.enums import Unit
from ...utils.time import Time as _Time

# Namespace used for the <pyobs:value> wrapper in RPC
PYOBS_NS = "urn:pyobs:rpc:1"


# ---------------------------------------------------------------------------
# Single-value serialization
# ---------------------------------------------------------------------------


def value_to_xml(value: Any, type_hint: Any) -> ET.Element:
    """Serialize a Python value to an XML element using the pyobs vocabulary.

    The returned element is the *content* element (e.g. ``<double>``,
    ``<boolean>``, ``<{ns}state>``). The caller is responsible for wrapping
    it in whatever container the protocol requires.

    Args:
        value: Python value to serialize.
        type_hint: Type annotation for the value (used for disambiguation).

    Returns:
        XML element representing the value.
    """
    # Unwrap Annotated[T, ...]
    if get_origin(type_hint) is Annotated:
        type_hint = get_args(type_hint)[0]

    # Normalize numpy scalars (np.float64, np.int64, np.bool_, ...) to native
    # Python types. np.float64 subclasses float but repr()s as "np.float64(x)"
    # since numpy 2.0, which corrupts <double> text; numpy integer types don't
    # subclass int at all and would otherwise fall through to <string>.
    if isinstance(value, np.generic):
        value = value.item()

    # None / void
    if value is None:
        elem = ET.Element("nil")
        return elem

    # bool (before int — bool is subclass of int)
    if isinstance(value, bool):
        elem = ET.Element("boolean")
        elem.text = "true" if value else "false"
        return elem

    # int
    if isinstance(value, int):
        elem = ET.Element("int")
        elem.text = str(value)
        return elem

    # float
    if isinstance(value, float):
        elem = ET.Element("double")
        elem.text = repr(value)
        return elem

    # str
    if isinstance(value, str):
        elem = ET.Element("string")
        elem.text = value
        return elem

    # StrEnum
    if isinstance(value, StrEnum):
        elem = ET.Element("string")
        elem.text = value.value
        return elem

    # dataclass — serialize as <{namespace}state> with plain field children
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return _dataclass_to_xml(value)

    # list
    if isinstance(value, list):
        item_type = get_args(type_hint)[0] if type_hint and get_origin(type_hint) is list else Any
        items = ET.Element("items")
        for item in value:
            item_elem = ET.Element("item")
            item_elem.append(value_to_xml(item, item_type))
            items.append(item_elem)
        return items

    # tuple
    if isinstance(value, tuple):
        item_types = get_args(type_hint) if type_hint and get_origin(type_hint) is tuple else []
        tup = ET.Element("tuple")
        for i, item in enumerate(value):
            item_type = item_types[i] if i < len(item_types) else Any
            item_elem = ET.Element("item")
            item_elem.append(value_to_xml(item, item_type))
            tup.append(item_elem)
        return tup

    # dict
    if isinstance(value, dict):
        key_type, val_type = get_args(type_hint)[:2] if type_hint and get_origin(type_hint) is dict else (Any, Any)
        dct = ET.Element("dict")
        for k, v in value.items():
            entry = ET.Element("entry")
            key_elem = ET.Element("key")
            key_elem.append(value_to_xml(k, key_type))
            val_elem = ET.Element("val")
            val_elem.append(value_to_xml(v, val_type))
            entry.append(key_elem)
            entry.append(val_elem)
            dct.append(entry)
        return dct

    # fallback: stringify
    elem = ET.Element("string")
    elem.text = str(value)
    return elem


def xml_to_value(elem: ET.Element, type_hint: Any) -> Any:
    """Deserialize an XML element (produced by ``value_to_xml``) to a Python value.

    Handles the namespace stripping needed after ejabberd round-trips
    (plain ``<double>`` may arrive as ``{urn:pyobs:rpc:1}double``).

    Args:
        elem: XML element to deserialize.
        type_hint: Expected Python type.

    Returns:
        Deserialized Python value.
    """
    # Unwrap Annotated[T, ...]
    if get_origin(type_hint) is Annotated:
        type_hint = get_args(type_hint)[0]

    # Unwrap Optional[T] / T | None → T
    args = get_args(type_hint) if type_hint else ()
    if args and type(None) in args:
        non_none = [a for a in args if a is not type(None)]
        type_hint = non_none[0] if non_none else Any

    # Strip namespace from tag — ejabberd may re-serialize plain children
    # with the parent element's namespace prefix.
    tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag

    if tag == "nil":
        return None

    if tag == "boolean":
        return elem.text == "true"

    if tag == "int":
        return int(elem.text) if elem.text is not None else 0

    if tag == "double":
        return float(elem.text) if elem.text is not None else 0.0

    if tag == "string":
        text = elem.text or ""
        # cast to enum if type_hint is a StrEnum subclass
        if type_hint and isinstance(type_hint, type) and issubclass(type_hint, StrEnum):
            return type_hint(text)
        return text

    if tag == "items":
        item_type = get_args(type_hint)[0] if type_hint and get_origin(type_hint) is list else Any
        result = []
        # findall with namespace stripping — ejabberd may namespace <item> elements
        for item_elem in elem:
            if item_elem.tag.split("}")[-1] == "item":
                children = list(item_elem)
                if children:
                    result.append(xml_to_value(children[0], item_type))
        return result

    if tag == "tuple":
        item_types = get_args(type_hint) if type_hint and get_origin(type_hint) is tuple else []
        result = []
        i = 0
        for item_elem in elem:
            if item_elem.tag.split("}")[-1] == "item":
                item_type = item_types[i] if i < len(item_types) else Any
                children = list(item_elem)
                if children:
                    result.append(xml_to_value(children[0], item_type))
                i += 1
        return tuple(result)

    if tag == "dict":
        key_type, val_type = get_args(type_hint)[:2] if type_hint and get_origin(type_hint) is dict else (Any, Any)
        result = {}
        for entry in elem:
            if entry.tag.split("}")[-1] != "entry":
                continue
            key_elem = next((c for c in entry if c.tag.split("}")[-1] == "key"), None)
            val_elem = next((c for c in entry if c.tag.split("}")[-1] == "val"), None)
            key_children = list(key_elem) if key_elem is not None else []
            val_children = list(val_elem) if val_elem is not None else []
            if key_children and val_children:
                k = xml_to_value(key_children[0], key_type)
                v = xml_to_value(val_children[0], val_type)
                result[k] = v
        return result

    # dataclass / State — the element IS the dataclass root
    if type_hint and dataclasses.is_dataclass(type_hint):
        return _xml_to_dataclass(elem, type_hint)

    # fallback
    return elem.text


# ---------------------------------------------------------------------------
# Dataclass serialization (used by state pub/sub and by value_to_xml)
# ---------------------------------------------------------------------------


def _dataclass_to_xml(state: Any, namespace: str = PYOBS_NS, tag: str = "state") -> ET.Element:
    """Serialize a dataclass to ``<{namespace}state>`` with plain field children.

    Each field is serialized using ``value_to_xml`` so the full vocabulary
    (nested dataclasses, lists, enums, etc.) is supported.

    Args:
        state: Dataclass instance to serialize.
        namespace: XML namespace for the root element.

    Returns:
        ``<{namespace}state>`` element.
    """
    root = ET.Element(f"{{{namespace}}}{tag}")
    hints = get_type_hints(type(state), include_extras=True)
    for f in dataclasses.fields(state):
        field_val = getattr(state, f.name)
        field_type = hints.get(f.name, Any)
        # Unwrap Annotated
        if get_origin(field_type) is Annotated:
            field_type = get_args(field_type)[0]
        child = ET.Element(f.name)
        child.append(value_to_xml(field_val, field_type))
        root.append(child)
    return root


def _xml_to_dataclass(elem: ET.Element, state_cls: type) -> Any:
    """Deserialize a ``<{ns}state>`` element to a dataclass instance.

    Handles both plain and namespace-prefixed child elements (ejabberd
    round-trip artefact).

    Args:
        elem: Root ``<state>`` element.
        state_cls: Dataclass class to instantiate.

    Returns:
        Populated dataclass instance.
    """
    hints = get_type_hints(state_cls, include_extras=True)
    # Namespace from root tag for namespaced child lookup
    ns = elem.tag[1 : elem.tag.index("}")] if elem.tag.startswith("{") else ""

    kwargs = {}
    for f in dataclasses.fields(state_cls):
        # Try namespaced child first (ejabberd round-trip), then plain
        child = elem.find(f"{{{ns}}}{f.name}") if ns else None
        if child is None:
            child = elem.find(f.name)
        if child is None:
            continue

        field_type = hints.get(f.name, Any)
        # Unwrap Annotated
        if get_origin(field_type) is Annotated:
            field_type = get_args(field_type)[0]
        # Unwrap Optional
        ft_args = get_args(field_type)
        if ft_args and type(None) in ft_args:
            field_type = next(a for a in ft_args if a is not type(None))

        # The child element wraps the value — it may contain a vocabulary
        # element (post-round-trip: the child IS the value element) or
        # have sub-children (new format: child contains value_to_xml output).
        value_elems = list(child)
        if value_elems:
            # New format: child contains a value element
            kwargs[f.name] = xml_to_value(value_elems[0], field_type)
        elif child.text is not None:
            # Legacy format: child.text is the raw value string
            kwargs[f.name] = _parse_scalar(child.text, field_type)
        # else: field absent, keep default

    return state_cls(**kwargs)


def _parse_scalar(text: str, type_hint: Any) -> Any:
    """Parse a raw text value to the given type (legacy state format fallback)."""
    if type_hint is bool:
        return text == "true"
    if type_hint is int:
        return int(text)
    if type_hint is float:
        return float(text)
    if isinstance(type_hint, type) and issubclass(type_hint, StrEnum):
        return type_hint(text)
    return text


# ---------------------------------------------------------------------------
# Interface schema (disco#info <pyobs:interface> blocks)
# ---------------------------------------------------------------------------


def _wire_type(hint: Any, enums: dict[str, type]) -> tuple[str, str | None]:
    """Map a Python type hint to a (wire_type_string, unit_string|None) pair."""
    origin = get_origin(hint)
    args = get_args(hint)

    # Annotated[T, ...] — extract optional Unit annotation
    if origin is Annotated:
        inner = args[0]
        unit = next((a for a in args[1:] if isinstance(a, Unit)), None)
        type_str, _ = _wire_type(inner, enums)
        return type_str, unit.value if unit else None

    # T | None → optional<T>  (handles typing.Union and builtin types.UnionType)
    if origin is Union or origin is _builtin_types.UnionType:
        non_none = [a for a in args if a is not type(None)]
        if len(non_none) == 1:
            inner_str, _ = _wire_type(non_none[0], enums)
            return f"optional<{inner_str}>", None
        return "any", None

    # list[T] → array<T>
    if origin is list:
        inner_str, _ = _wire_type(args[0] if args else Any, enums)
        return f"array<{inner_str}>", None

    # Primitives — bool before int (bool is a subclass of int)
    if hint is bool:
        return "bool", None
    if hint is int:
        return "int32", None
    if hint is float:
        return "float64", None
    if hint is str:
        return "string", None
    if hint is type(None):
        return "void", None

    # Time (pyobs's astropy.time.Time subclass)
    if isinstance(hint, type) and issubclass(hint, _Time):
        return "datetime", None

    # StrEnum subclass → enum(Name) + record for <types> block
    if isinstance(hint, type) and issubclass(hint, StrEnum) and hint is not StrEnum:
        enums[hint.__name__] = hint
        return f"enum({hint.__name__})", None

    # dataclass → struct<Name>
    if dataclasses.is_dataclass(hint) and isinstance(hint, type):
        return f"struct<{hint.__name__}>", None

    return "any", None


def _interface_schema_to_xml(interface: type) -> ET.Element:
    """Build the <{ns}interface> disco#info schema element for one Interface subclass."""
    ns = f"urn:pyobs:interface:{interface.__name__}:{interface.version}"
    root = ET.Element(f"{{{ns}}}interface", attrib={"name": interface.__name__})

    enums: dict[str, type] = {}

    # Collect <command> elements from abstract methods, MRO base-first
    seen: set[str] = set()
    cmd_elems: list[ET.Element] = []

    for base in reversed(interface.__mro__):
        if base in (object, _Interface):
            continue
        for name, member in sorted(base.__dict__.items()):
            if name.startswith("_") or name in seen:
                continue
            if not getattr(member, "__isabstractmethod__", False):
                continue
            seen.add(name)

            try:
                hints = get_type_hints(member, include_extras=True)
                sig = inspect.signature(member)
            except Exception:
                continue

            cmd = ET.Element("command", attrib={"name": name})
            for param_name, param in sig.parameters.items():
                if param_name == "self" or param.kind in (param.VAR_KEYWORD, param.VAR_POSITIONAL):
                    continue
                if param_name not in hints:
                    continue
                type_str, unit_str = _wire_type(hints[param_name], enums)
                attrib: dict[str, str] = {"name": param_name, "type": type_str}
                if unit_str:
                    attrib["unit"] = unit_str
                ET.SubElement(cmd, "parameter", attrib=attrib)

            cmd_elems.append(cmd)

    # Build <state> element (after commands, so enum collection covers both)
    state_elem: ET.Element | None = None
    if getattr(interface, "state", None) is not None and dataclasses.is_dataclass(interface.state):
        state_node = f"state/{interface.__name__}/{interface.version}"
        state_elem = ET.Element("state", attrib={"node": state_node})
        try:
            state_hints = get_type_hints(interface.state, include_extras=True)
        except Exception:
            state_hints = {}
        for f in dataclasses.fields(interface.state):
            type_str, unit_str = _wire_type(state_hints.get(f.name, Any), enums)
            fattrib: dict[str, str] = {"name": f.name, "type": type_str}
            if unit_str:
                fattrib["unit"] = unit_str
            ET.SubElement(state_elem, "field", attrib=fattrib)

    # Emit in order: <types> → <command>... → <state>
    if enums:
        types_elem = ET.SubElement(root, "types")
        for enum_name, enum_cls in sorted(enums.items()):
            enum_elem = ET.SubElement(types_elem, "enum", attrib={"name": enum_name})
            for member in enum_cls:
                val_elem = ET.SubElement(enum_elem, "value")
                val_elem.text = member.value

    for cmd in cmd_elems:
        root.append(cmd)

    if state_elem is not None:
        root.append(state_elem)

    return root


def _event_schema_to_xml(event_cls: type) -> ET.Element:
    """Build the <{ns}event> disco#info schema element for one Event subclass."""
    ns = f"urn:pyobs:event:{event_cls.__name__}:{event_cls.version}"
    root = ET.Element(f"{{{ns}}}event", attrib={"name": event_cls.__name__})

    enums: dict[str, type] = {}
    field_elems: list[ET.Element] = []

    try:
        hints = get_type_hints(event_cls.__init__, include_extras=True)
        sig = inspect.signature(event_cls.__init__)
    except Exception:
        return root

    for param_name, param in sig.parameters.items():
        if param_name == "self" or param.kind in (param.VAR_KEYWORD, param.VAR_POSITIONAL):
            continue
        if param_name not in hints:
            continue
        type_str, unit_str = _wire_type(hints[param_name], enums)
        attrib: dict[str, str] = {"name": param_name, "type": type_str}
        if unit_str:
            attrib["unit"] = unit_str
        field_elems.append(ET.Element("field", attrib=attrib))

    if enums:
        types_elem = ET.SubElement(root, "types")
        for enum_name, enum_cls in sorted(enums.items()):
            enum_elem = ET.SubElement(types_elem, "enum", attrib={"name": enum_name})
            for member in enum_cls:
                val_elem = ET.SubElement(enum_elem, "value")
                val_elem.text = member.value

    for f in field_elems:
        root.append(f)

    return root


__all__ = [
    "PYOBS_NS",
    "value_to_xml",
    "xml_to_value",
    "_dataclass_to_xml",
    "_xml_to_dataclass",
    "_interface_schema_to_xml",
    "_event_schema_to_xml",
]
