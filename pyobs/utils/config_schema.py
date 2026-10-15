from __future__ import annotations

import dataclasses
import enum
import functools
import math
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


ChoiceValue = str | int | float | bool


@dataclasses.dataclass
class ConfigChoice:
    value: ChoiceValue
    label: str


def choice_values_equal(left: Any, right: Any) -> bool:
    """Match JSON scalars without confusing booleans, numbers and strings."""
    if type(left) in (int, float) and type(right) in (int, float):
        return left == right
    return type(left) is type(right) and left == right


def _choice_value(value: Any) -> ChoiceValue:
    if isinstance(value, enum.Enum):
        value = value.value
    if type(value) not in (str, int, float, bool) or (type(value) is float and not math.isfinite(value)):
        raise TypeError(f"Unsupported configuration choice: {value!r}")
    return value


def _enum_schema(values: typing.Iterable[Any], default: Any) -> ConfigFieldSchema:
    choices = [ConfigChoice(_choice_value(value), str(_choice_value(value))) for value in values]
    if isinstance(default, enum.Enum):
        default = _choice_value(default)
    return ConfigFieldSchema(
        type="enum", options=[str(choice.value) for choice in choices], default=default, choices=choices
    )


def _apply_choice_labels(schema: ConfigFieldSchema, metadata: Any) -> None:
    if schema.choices is None or not isinstance(metadata, typing.Mapping):
        return
    records = metadata.get("x-pyobs-choices")
    if not isinstance(records, list):
        return
    for choice in schema.choices:
        labels = {
            record["label"]
            for record in records
            if isinstance(record, dict)
            and isinstance(record.get("label"), str)
            and choice_values_equal(record.get("value"), choice.value)
        }
        if len(labels) == 1:
            choice.label = labels.pop()


@dataclasses.dataclass
class ConfigFieldSchema:
    type: str
    unit: Unit | None = None
    options: list[str] | None = None
    default: Any | None = None
    nested: dict[str, ConfigFieldSchema] | None = None
    level: AccessLevel = AccessLevel.BASIC
    description: str | None = None
    choices: list[ConfigChoice] | None = None


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
        _apply_choice_labels(schema, f.metadata)
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
        return _enum_schema(annotation, default if default is not dataclasses.MISSING else None)

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
        _apply_choice_labels(schema, info.json_schema_extra)
        fields[name] = schema
    return ConfigSchema(fields=fields)


def _pydantic_field_level(json_schema_extra: Any) -> AccessLevel:
    if isinstance(json_schema_extra, dict) and "level" in json_schema_extra:
        return _coerce_level(json_schema_extra["level"])
    return AccessLevel.BASIC


def _pydantic_field_description(info: Any) -> str | None:
    """Prefer description metadata when supplied; otherwise use Field(description=...)."""
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
        return _enum_schema(get_args(annotation), default)

    if isinstance(annotation, type) and issubclass(annotation, enum.Enum):
        return _enum_schema(annotation, default)

    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return ConfigFieldSchema(type="object", nested=pydantic_to_schema(annotation).fields)

    if annotation is dict or origin is dict:
        return ConfigFieldSchema(type="object", default=default)

    type_name = {str: "str", int: "int", float: "float", bool: "bool"}.get(annotation)
    if type_name is None:
        raise TypeError(f"Unsupported config field type for schema: {annotation!r}")

    return ConfigFieldSchema(type=type_name, default=default)


__all__ = [
    "ConfigChoice",
    "ConfigFieldSchema",
    "ConfigSchema",
    "choice_values_equal",
    "dataclass_to_schema",
    "pydantic_to_schema",
]
