from __future__ import annotations

import datetime
from abc import ABCMeta
from typing import Any, Self, TypeVar

from astroplan import Observer
from pydantic import BaseModel as PydanticBaseModel
from pydantic import ConfigDict, PrivateAttr, model_serializer, model_validator
from pydantic_core.core_schema import SerializationInfo, ValidationInfo, ValidatorFunctionWrapHandler

from pyobs.comm import Comm
from pyobs.object import PrivateAttrMixin
from pyobs.vfs import VirtualFileSystem

"""Class of an Object."""
ObjectClass = TypeVar("ObjectClass")


class BaseModel(PydanticBaseModel, PrivateAttrMixin):
    """Pydantic base model for pyobs classes that need to be serialized."""

    _timezone: datetime.tzinfo | None = PrivateAttr(default=None)
    _vfs: VirtualFileSystem | None = PrivateAttr(default=None)
    _observer: Observer | None = PrivateAttr(default=None)
    _comm: Comm | None = PrivateAttr(default=None)

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")

    @model_validator(mode="after")
    def _inject_context_into_children(self, info: ValidationInfo) -> Self:
        if info.context is not None:
            self._comm = info.context.get("comm")
            self._observer = info.context.get("observer")
            self._vfs = info.context.get("vfs")
            self._timezone = info.context.get("timezone")
        return self


class PolymorphicBaseModel(BaseModel, metaclass=ABCMeta):  # type: ignore[misc]
    """Pydantic base model for pyobs sub classes that need to be serialized."""

    def _flat_field_spec(self, spec: Any, info_kwarg: str) -> set[str] | None:
        """Reduce a pydantic `exclude=`/`include=` spec to a flat set of field names.

        `inject_class_on_serialization` hand-builds its output dict instead of delegating to
        `handler`, so it also has to hand-apply `exclude`/`include` itself -- pydantic's spec
        grammar supports nested dicts (partial excludes on sub-fields) and integer/`__all__` keys
        (per-element excludes on sequences), forwarded into each field's own serialization. Doing
        that generically would mean reimplementing a chunk of pydantic-core's own traversal; since
        every current caller only ever passes a flat set of top-level field names (see
        pyobs-core#855), only that flat form is supported. Anything else raises rather than
        silently ignoring or partially applying the spec.
        """
        if spec is None:
            return None
        if isinstance(spec, set | frozenset):
            return set(spec)
        if isinstance(spec, dict) and all(v is True for v in spec.values()):
            return set(spec.keys())
        raise NotImplementedError(
            f"PolymorphicBaseModel.model_dump() only supports a flat field-name {info_kwarg}= "
            f"(no nested specs) -- got {spec!r} for {type(self).__name__}; see pyobs-core#855"
        )

    @model_serializer(mode="wrap")
    def inject_class_on_serialization(
        self, handler: ValidatorFunctionWrapHandler, info: SerializationInfo
    ) -> dict[str, Any]:
        # Collect fields from the concrete runtime type to avoid Pydantic v2
        # resolving field schemas against the abstract base type when nested in a parent model
        if info.exclude_computed_fields and type(self).__pydantic_decorators__.computed_fields:
            raise NotImplementedError(
                f"PolymorphicBaseModel.model_dump() doesn't support exclude_computed_fields= for "
                f"{type(self).__name__}; see pyobs-core#855"
            )
        exclude = self._flat_field_spec(info.exclude, "exclude")
        include = self._flat_field_spec(info.include, "include")
        fields = type(self).model_fields
        names = [n for n in fields if (include is None or n in include) and (exclude is None or n not in exclude)]

        result: dict[str, Any] = {}
        for name in names:
            value = getattr(self, name)
            if info.exclude_none and value is None:
                continue
            if info.exclude_unset and name not in self.model_fields_set:
                continue
            if info.exclude_defaults and value == fields[name].get_default(call_default_factory=True):
                continue
            alias = fields[name].alias
            key = alias if (info.by_alias and alias) else name
            result[key] = value
        result["class"] = f"{self.__module__}.{self.__class__.__name__}"
        return result

    @model_validator(mode="wrap")
    @classmethod
    def retrieve_class_on_deserialization(
        cls, value: Any, handler: ValidatorFunctionWrapHandler, info: ValidationInfo
    ) -> Any:
        """Get the correct class for this model and run model_validate on that class with the current context."""
        if isinstance(value, dict):
            from pyobs.object import get_class_from_string

            modified_value = value.copy()
            sub_cls_name = modified_value.pop("class", None)
            if sub_cls_name is not None:
                klass = get_class_from_string(sub_cls_name)
                return klass.model_validate(modified_value, context=info.context, by_alias=True)
        return handler(value)


def resolve_polymorphic_type_shorthand(
    config: dict[str, Any], available: list[str], module_prefix: str, type_suffix: str
) -> None:
    """Resolve a `type` shorthand key (e.g. `type: Airmass`) into an explicit `class` key that
    `PolymorphicBaseModel.retrieve_class_on_deserialization` can use, in place. No-op if `config`
    has no `type` key.

    Args:
        config: Config dict to resolve, mutated in place.
        available: Class names to match `type` against (case-insensitively, with `type_suffix`
            appended).
        module_prefix: Dotted module path the matched class lives in.
        type_suffix: Suffix appended to `type` before matching against `available`, e.g. "merit".

    Raises:
        ValueError: If `type` doesn't match any class in `available`.
    """
    if "type" not in config:
        return
    available_lower = [c.lower() for c in available]
    try:
        idx = available_lower.index(config["type"].lower() + type_suffix.lower())
    except ValueError:
        raise ValueError(f"Invalid {type_suffix.lower()} type: {config['type']}")
    config["class"] = f"{module_prefix}.{available[idx]}"
    del config["type"]


__all__ = ["BaseModel", "PolymorphicBaseModel", "resolve_polymorphic_type_shorthand"]
