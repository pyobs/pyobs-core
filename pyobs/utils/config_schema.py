from __future__ import annotations

import dataclasses
import enum
import functools
from typing import Annotated, Any, get_args, get_origin, get_type_hints

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


__all__ = ["ConfigFieldSchema", "ConfigSchema", "dataclass_to_schema"]
