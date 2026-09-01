from __future__ import annotations

import dataclasses
import enum
import logging
import typing
from typing import Annotated, Any

from pyobs.interfaces import ConfigAppliedState, IStructuredConfig
from pyobs.modules import Module
from pyobs.utils.config_schema import dataclass_to_schema
from pyobs.utils.enums import Unit

log = logging.getLogger(__name__)


class DummyOperatingMode(enum.Enum):
    """Selectable mode for the dummy structured config's `mode` field."""

    TRACK = "track"
    PARK = "park"
    SLEW = "slew"


@dataclasses.dataclass
class DummyNestedConfig:
    """A nested sub-config, so the schema exercises `type="object"` with `nested`."""

    label: str = "nested"
    threshold: int = 5
    active: bool = True


@dataclasses.dataclass
class DummyStructuredConfigData:
    """Covers every `ConfigFieldSchema` type at least once: str, int, a float with a unit,
    bool, an enum, and a nested dataclass."""

    name: str = "dummy"
    count: int = 1
    offset: Annotated[float, Unit.ARCSEC] = 0.0
    verbose: bool = False
    mode: DummyOperatingMode = DummyOperatingMode.TRACK
    nested: DummyNestedConfig = dataclasses.field(default_factory=DummyNestedConfig)


def _from_dict(cls: type, data: Any) -> Any:
    """Recursively build a dataclass instance from a nested dict, raising ValueError on any
    schema mismatch (unknown field, wrong type, invalid enum value) per IStructuredConfig's
    documented set_config contract."""
    if not isinstance(data, dict):
        raise ValueError(f"Expected a dict for {cls.__name__}, got {type(data).__name__}")

    hints = typing.get_type_hints(cls, include_extras=True)
    field_names = {f.name for f in dataclasses.fields(cls)}
    unknown = set(data) - field_names
    if unknown:
        raise ValueError(f"Unknown field(s) for {cls.__name__}: {sorted(unknown)}")

    kwargs: dict[str, Any] = {}
    for name, value in data.items():
        annotation = hints[name]
        if typing.get_origin(annotation) is Annotated:
            annotation = typing.get_args(annotation)[0]

        if dataclasses.is_dataclass(annotation):
            kwargs[name] = _from_dict(annotation, value)
        elif isinstance(annotation, type) and issubclass(annotation, enum.Enum):
            try:
                kwargs[name] = annotation(value)
            except ValueError:
                raise ValueError(f"Invalid value for {cls.__name__}.{name}: {value!r}") from None
        elif annotation is float and isinstance(value, int) and not isinstance(value, bool):
            kwargs[name] = float(value)
        else:
            if not isinstance(value, annotation) or (annotation is int and isinstance(value, bool)):
                raise ValueError(
                    f"Invalid type for {cls.__name__}.{name}: expected {annotation.__name__}, "
                    f"got {type(value).__name__}"
                )
            kwargs[name] = value

    return cls(**kwargs)


def _to_dict(instance: Any) -> dict[str, Any]:
    """Inverse of _from_dict: nested dataclasses become nested dicts, enums become their value."""
    result: dict[str, Any] = {}
    for f in dataclasses.fields(instance):
        value = getattr(instance, f.name)
        if dataclasses.is_dataclass(value):
            result[f.name] = _to_dict(value)
        elif isinstance(value, enum.Enum):
            result[f.name] = value.value
        else:
            result[f.name] = value
    return result


class DummyStructuredConfig(Module, IStructuredConfig):
    """A dummy module implementing IStructuredConfig, with no hardware behind it.

    Exists so a schema-driven config widget (e.g. pyobs-gui's StructuredConfigWidget) has
    something to actually run against for manual verification: at the time this was added,
    the only other IStructuredConfig consumer anywhere was pyobs-iagvt's FTS module, which
    isn't available in a headless/dummy-fleet dev setup."""

    __module__ = "pyobs.modules.utils"

    def __init__(self, **kwargs: Any):
        """Creates a new dummy structured-config module."""
        super().__init__(**kwargs)
        self._config = DummyStructuredConfigData()

    async def open(self) -> None:
        """Open module."""
        await Module.open(self)
        await self.comm.set_capabilities(IStructuredConfig, dataclass_to_schema(DummyStructuredConfigData))
        await self._publish_state()

    async def set_config(self, config: dict[str, Any], **kwargs: Any) -> None:
        """Apply a full structured config to this module.

        Args:
            config: Nested dict matching DummyStructuredConfigData's schema.

        Raises:
            ValueError: If config doesn't match the schema, or values fail validation.
        """
        self._config = _from_dict(DummyStructuredConfigData, config)
        await self._publish_state()

    async def _publish_state(self) -> None:
        await self.comm.set_state(IStructuredConfig, ConfigAppliedState(config=_to_dict(self._config)))


__all__ = ["DummyStructuredConfig", "DummyStructuredConfigData", "DummyNestedConfig", "DummyOperatingMode"]
