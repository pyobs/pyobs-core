# `IStructuredConfig`: bulk structured config for pyobs modules

## Motivation

`IConfig` (unchanged, stays as-is) already lets any module get/set config
**per field**, with per-field capability introspection
(`get_config_caps` → `dict[str, tuple[bool, bool, bool]]` for
readable/writable/has-options). That's the right model for flat,
independently-tunable values.

`pyobs-iagvt`'s siderostat driver needs something different: it holds one
config **dataclass** (potentially nested — sub-dataclasses for things like a
pointing model) that gets pushed and applied as a unit, not field-by-field.
`IStructuredConfig` is a new interface for that case. It is *not* a
replacement for `IConfig` — the two coexist, used for different shapes of
config.

Repo: `pyobs-core` (this repo). All paths below relative to repo root.

## Design summary

Same split pyobs already uses everywhere else (see `pyobs/interfaces/ICooling.py`
for the reference pattern):

- **`capabilities`** (`ConfigSchema`) — static, describes *shape*: field
  names, types, units, allowed options, nesting. Fetched via the existing
  generic `Comm.get_capabilities(module, interface)` path
  (`pyobs/comm/comm.py:496`) — **no changes needed there**, it already
  deserializes whatever dataclass type an interface declares as
  `capabilities`.
- **`state`** (`ConfigAppliedState`) — live, describes *current values*.
  Published via the existing pub-sub state mechanism, same as
  `CoolingState`.
- **`set_config(...)`** — the only RPC method. Call-only, no getter (readback
  comes from subscribing to `state`, not from a get RPC — this mirrors
  `ICooling.set_cooling`, which is also call-only).

No values ever live inside `ConfigSchema`/`ConfigFieldSchema` — schema is
shape-only. Values only ever live in `ConfigAppliedState.config`.

## 1. Recursive `ConfigValue`

`pyobs/interfaces/IConfig.py` currently defines `ConfigValue` one level deep
(`dict[str, ConfigScalar]`). Needed for `IStructuredConfig` to support nested
dataclasses. Add this as a new type alias — **do not change `IConfig`'s
existing usage**, just make the recursive version available for
`IStructuredConfig` to use:

```python
ConfigValue = ConfigScalar | list["ConfigValue"] | dict[str, "ConfigValue"]
```

Decide during implementation whether to widen `IConfig`'s existing
`ConfigValue` in place (if nothing depends on the flat version) or introduce
this as a separately-named alias to avoid touching `IConfig` at all. Prefer
the latter unless a quick grep shows it's safe.

## 2. New file: `pyobs/utils/config_schema.py`

Auto-derives a schema from an arbitrary (possibly nested) dataclass, so
module authors never hand-write `ConfigSchema` — it's generated from the
same dataclass they already use for their real config.

```python
from __future__ import annotations
import dataclasses
import enum
from typing import Annotated, Any, get_args, get_origin, get_type_hints
from pyobs.utils.enums import Unit


@dataclasses.dataclass
class ConfigFieldSchema:
    type: str
    unit: Unit | None = None
    options: list[str] | None = None
    default: Any | None = None
    nested: dict[str, "ConfigFieldSchema"] | None = None


@dataclasses.dataclass
class ConfigSchema:
    fields: dict[str, ConfigFieldSchema]


def dataclass_to_schema(cls: type) -> ConfigSchema:
    """Recursively derive a ConfigSchema from a dataclass type.

    Handles: plain scalars (str/int/float/bool), Enum-typed fields (→
    type="enum" with `options`), Annotated[T, Unit.X] (→ populates `unit`),
    and nested dataclasses (→ type="object" with `nested`).
    Raises a clear error for unsupported field types rather than silently
    guessing — this schema is consumed by GUI rendering code, silent
    fallbacks there are worse than a loud failure here.
    """
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
```

Notes for implementation:
- `mode: str  # one of "track", "park", "slew"` in freeform prose should
  really be a proper `enum.Enum` in the real dataclass, not a bare `str`
  with a comment — that's what lets `dataclass_to_schema` populate
  `options` automatically. Worth enforcing this as a convention: any config
  field that should render as a dropdown must be an actual Enum subclass.
- Cache the derived schema per class (e.g. `functools.lru_cache` keyed on
  `cls`) since it's static per type — no need to recompute per RPC call.

## 3. New file: `pyobs/interfaces/IStructuredConfig.py`

Follow the exact structure of `pyobs/interfaces/ICooling.py`:

```python
from __future__ import annotations
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import Any
from ..utils.time import Time
from ..utils.config_schema import ConfigSchema, ConfigFieldSchema  # re-export
from .interface import Interface
from .IConfig import ConfigScalar

ConfigValue = ConfigScalar | list["ConfigValue"] | dict[str, "ConfigValue"]


@dataclass
class ConfigAppliedState:
    config: dict[str, ConfigValue]
    time: Time = field(default_factory=Time.now)


class IStructuredConfig(Interface, metaclass=ABCMeta):
    """The module accepts a whole structured (possibly nested) config
    object in one call, rather than per-field get/set (see IConfig for
    the per-field variant)."""

    __module__ = "pyobs.interfaces"

    capabilities = ConfigSchema
    state = ConfigAppliedState

    @abstractmethod
    async def set_config(self, config: dict[str, ConfigValue], **kwargs: Any) -> None:
        """Apply a full structured config to this module.

        Args:
            config: Nested dict matching this module's ConfigSchema
                (fetch via get_capabilities). Values are validated and
                deserialized into the module's internal config dataclass.

        Raises:
            ValueError: If config doesn't match the module's schema, or
                values fail validation.
        """
        ...


__all__ = ["IStructuredConfig", "ConfigAppliedState", "ConfigSchema", "ConfigFieldSchema"]
```

Register it in `pyobs/interfaces/__init__.py` alongside the other interface
imports (this is required for the existing `inspect.getmembers(pyobs.interfaces, ...)`
resolution in `pyobs/comm/comm.py` and `pyobs/comm/xmpp/xmppcomm.py` to find it
— see the earlier discussion of that mechanism).

## 4. Consumer side: `pyobs-iagvt`

In the siderostat module (`siderostat.py`):

1. Define `SiderostatConfig` (and any nested sub-dataclasses, e.g.
   `PointingModel`) as real dataclasses with proper typing (`Annotated[float, Unit.ARCSEC]`
   for physical quantities, real `Enum` subclasses for anything
   dropdown-like).
2. Implement `IStructuredConfig`:
   - `capabilities` is derived once via `dataclass_to_schema(SiderostatConfig)`.
   - `set_config(config)` deserializes the incoming dict into a
     `SiderostatConfig` instance, applies it to the hardware, then publishes
     a fresh `ConfigAppliedState` with the new values.
3. On startup / whenever the live config changes for any reason (not just
   via `set_config`, e.g. a hardware-side change), publish
   `ConfigAppliedState` so subscribed GUI clients stay in sync.

## 5. Testing checklist

- `dataclass_to_schema` round-trips a nested dataclass (including a
  dataclass field, an Enum field, and an `Annotated[float, Unit.X]` field)
  into the expected `ConfigSchema` shape.
- A dataclass with an unsupported field type (e.g. a raw `datetime`) raises
  `TypeError` from `dataclass_to_schema` rather than silently producing a
  wrong schema.
- `IStructuredConfig.set_config` on a test module round-trips: call
  `set_config({...})`, then read back the next published `ConfigAppliedState`
  and confirm it matches.
- `Comm.get_capabilities(module, IStructuredConfig)` returns the expected
  `ConfigSchema` for a module implementing it — confirms the existing
  generic capabilities path needs no changes.

## Explicitly out of scope for this change

- No changes to `IConfig` (`pyobs/interfaces/IConfig.py`) or its use in
  `pyobs/modules/module.py` — it keeps its current per-field get/set
  semantics unchanged.
- No merge of `IConfig` into `IModule` — considered and rejected; `IConfig`
  stays a separate interface.
