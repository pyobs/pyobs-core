from __future__ import annotations

import dataclasses
import enum
import functools
import types
import typing
from typing import Annotated, Any, get_args, get_origin, get_type_hints

from pydantic import BaseModel
from pydantic_core import PydanticUndefined

from pyobs.utils.enums import Unit


@dataclasses.dataclass
class ConfigFieldSchema:
    type: str
    unit: Unit | None = None
    options: list[str] | None = None
    default: Any | None = None
    nested: dict[str, ConfigFieldSchema] | None = None


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
        fields[f.name] = _field_schema(hints[f.name], f.default)
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
        fields[name] = _pydantic_field_schema(info.annotation, default)
    return ConfigSchema(fields=fields)


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
