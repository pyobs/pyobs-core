from __future__ import annotations

import dataclasses
import enum
import functools
import types
import typing
from typing import Annotated, Any, get_args, get_origin, get_type_hints

from pydantic import BaseModel
from pydantic_core import PydanticUndefined

from pyobs.utils.enums import AccessLevel, Unit


def _coerce_level(value: Any) -> AccessLevel:
    """Coerce a raw level value (an int, or any IntEnum with matching member values -- e.g. a
    consumer's own local AccessLevel copy per specs/steering/gui-field-access-levels.md) into
    this module's AccessLevel. Falls back to BASIC for anything missing or unrecognized, so a
    field that never opted into this feature keeps rendering exactly as before.
    """
    try:
        return AccessLevel(int(value))
    except (TypeError, ValueError):
        return AccessLevel.BASIC


@dataclasses.dataclass
class ConfigFieldSchema:
    type: str
    unit: Unit | None = None
    options: list[str] | None = None
    default: Any | None = None
    nested: dict[str, ConfigFieldSchema] | None = None
    level: AccessLevel = AccessLevel.BASIC
    description: str | None = None


@dataclasses.dataclass
class ConfigSchema:
    fields: dict[str, ConfigFieldSchema]


@functools.cache
def dataclass_to_schema(cls: type) -> ConfigSchema:
    """Recursively derive a ConfigSchema from a dataclass type.

    Handles: plain scalars (str/int/float/bool), Enum-typed fields (→
    type="enum" with `options`), Annotated[T, Unit.X] (→ populates `unit`),
    and nested dataclasses (→ type="object" with `nested`).
    Raises a clear error for unsupported field types rather than silently
    guessing — this schema is consumed by GUI rendering code, silent
    fallbacks there are worse than a loud failure here.
    """
    if not dataclasses.is_dataclass(cls):
        raise TypeError(f"Not a dataclass: {cls!r}")

    hints = get_type_hints(cls, include_extras=True)
    fields: dict[str, ConfigFieldSchema] = {}
    for f in dataclasses.fields(cls):
        schema = _field_schema(hints[f.name], f.default)
        schema.level = _coerce_level(f.metadata.get("level", AccessLevel.BASIC))
        schema.description = f.metadata.get("description")
        fields[f.name] = schema
    return ConfigSchema(fields=fields)


def _field_schema(annotation: Any, default: Any) -> ConfigFieldSchema:
    unit = None
    origin = get_origin(annotation)
    if origin is Annotated:
        annotation, *extras = get_args(annotation)
        unit = next((e for e in extras if isinstance(e, Unit)), None)

    if dataclasses.is_dataclass(annotation):
        nested_schema = dataclass_to_schema(annotation)
        return ConfigFieldSchema(type="object", nested=nested_schema.fields)

    if isinstance(annotation, type) and issubclass(annotation, enum.Enum):
        return ConfigFieldSchema(
            type="enum",
            options=[e.value for e in annotation],
            default=default if default is not dataclasses.MISSING else None,
        )

    type_name = {str: "str", int: "int", float: "float", bool: "bool"}.get(annotation)
    if type_name is None:
        raise TypeError(f"Unsupported config field type for schema: {annotation!r}")

    return ConfigFieldSchema(
        type=type_name,
        unit=unit,
        default=default if default is not dataclasses.MISSING else None,
    )


@functools.cache
def pydantic_to_schema(cls: type[BaseModel]) -> ConfigSchema:
    """Recursively derive a ConfigSchema from a Pydantic BaseModel.

    Counterpart to dataclass_to_schema, for config objects that need to be
    Pydantic models (e.g. for their own validation) rather than plain
    dataclasses. Handles: plain scalars (str/int/float/bool), Literal-typed
    fields (-> type="enum" with `options`), Optional[...]/`X | None`
    (unwrapped), nested BaseModel fields (-> type="object" with `nested`),
    and opaque `dict` fields (-> type="object" with no nested schema, for
    freeform blobs). Raises for anything else unhandled, for the same
    reason as dataclass_to_schema: this schema drives GUI rendering, and a
    silent fallback there is worse than a loud failure here.
    """
    if not (isinstance(cls, type) and issubclass(cls, BaseModel)):
        raise TypeError(f"Not a Pydantic model: {cls!r}")

    fields: dict[str, ConfigFieldSchema] = {}
    for name, info in cls.model_fields.items():
        default = None if info.default is PydanticUndefined else info.default
        schema = _pydantic_field_schema(info.annotation, default)
        schema.level = _pydantic_field_level(info.json_schema_extra)
        schema.description = _pydantic_field_description(info)
        fields[name] = schema
    return ConfigSchema(fields=fields)


def _pydantic_field_level(json_schema_extra: Any) -> AccessLevel:
    if isinstance(json_schema_extra, dict) and "level" in json_schema_extra:
        return _coerce_level(json_schema_extra["level"])
    return AccessLevel.BASIC


def _pydantic_field_description(info: Any) -> str | None:
    """FTSConfigMain (pyftscontrol) puts the description inside json_schema_extra alongside
    level, rather than using Pydantic's own Field(description=...) -- prefer that convention
    when present, but fall back to the native `description` for a model that uses it directly.
    """
    extra = info.json_schema_extra
    if isinstance(extra, dict) and isinstance(extra.get("description"), str):
        return extra["description"]
    return info.description


def _pydantic_field_schema(annotation: Any, default: Any) -> ConfigFieldSchema:
    origin = get_origin(annotation)

    if origin is typing.Union or origin is types.UnionType:
        args = [a for a in get_args(annotation) if a is not type(None)]
        if len(args) == 1:
            return _pydantic_field_schema(args[0], default)

    if origin is typing.Literal:
        return ConfigFieldSchema(type="enum", options=[str(v) for v in get_args(annotation)], default=default)

    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return ConfigFieldSchema(type="object", nested=pydantic_to_schema(annotation).fields)

    if annotation is dict or origin is dict:
        return ConfigFieldSchema(type="object", default=default)

    type_name = {str: "str", int: "int", float: "float", bool: "bool"}.get(annotation)
    if type_name is None:
        raise TypeError(f"Unsupported config field type for schema: {annotation!r}")

    return ConfigFieldSchema(type=type_name, default=default)


__all__ = ["ConfigFieldSchema", "ConfigSchema", "dataclass_to_schema", "pydantic_to_schema"]
