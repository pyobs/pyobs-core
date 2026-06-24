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
from enum import StrEnum
from typing import Annotated, Any, get_args, get_origin, get_type_hints

from slixmpp.xmlstream import ET

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

    # Unwrap Optional[T] / T | None → T, then Annotated[T, ...]
    args = get_args(type_hint) if type_hint else ()
    if args and type(None) in args:
        non_none = [a for a in args if a is not type(None)]
        type_hint = non_none[0] if non_none else Any
    # Unwrap Annotated after Optional
    if get_origin(type_hint) is Annotated:
        type_hint = get_args(type_hint)[0]

    # Strip namespace from tag — ejabberd may re-serialize plain children
    # with the parent element's namespace prefix.
    tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag

    if tag == "nil":
        return None

    if tag == "boolean":
        return elem.text == "true"

    if tag == "int":
        return int(elem.text)

    if tag == "double":
        return float(elem.text)

    if tag == "string":
        text = elem.text or ""
        # cast to enum if type_hint is a StrEnum subclass
        if type_hint and isinstance(type_hint, type) and issubclass(type_hint, StrEnum):
            return type_hint(text)
        return text

    if tag == "items":
        item_type = get_args(type_hint)[0] if type_hint and get_origin(type_hint) is list else Any
        result = []
        for item_elem in elem.findall("item"):
            children = list(item_elem)
            if children:
                result.append(xml_to_value(children[0], item_type))
        return result

    if tag == "tuple":
        item_types = get_args(type_hint) if type_hint and get_origin(type_hint) is tuple else []
        result = []
        for i, item_elem in enumerate(elem.findall("item")):
            item_type = item_types[i] if i < len(item_types) else Any
            children = list(item_elem)
            if children:
                result.append(xml_to_value(children[0], item_type))
        return tuple(result)

    if tag == "dict":
        key_type, val_type = get_args(type_hint)[:2] if type_hint and get_origin(type_hint) is dict else (Any, Any)
        result = {}
        for entry in elem.findall("entry"):
            key_children = list(entry.find("key") or [])
            val_children = list(entry.find("val") or [])
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


def _dataclass_to_xml(state: Any, namespace: str = PYOBS_NS) -> ET.Element:
    """Serialize a dataclass to ``<{namespace}state>`` with plain field children.

    Each field is serialized using ``value_to_xml`` so the full vocabulary
    (nested dataclasses, lists, enums, etc.) is supported.

    Args:
        state: Dataclass instance to serialize.
        namespace: XML namespace for the root element.

    Returns:
        ``<{namespace}state>`` element.
    """
    root = ET.Element(f"{{{namespace}}}state")
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
        # Unwrap Optional (T | None) first
        ft_args = get_args(field_type)
        if ft_args and type(None) in ft_args:
            field_type = next(a for a in ft_args if a is not type(None))
        # Unwrap Annotated[T, ...]
        if get_origin(field_type) is Annotated:
            field_type = get_args(field_type)[0]

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


__all__ = [
    "PYOBS_NS",
    "value_to_xml",
    "xml_to_value",
    "_dataclass_to_xml",
    "_xml_to_dataclass",
]
