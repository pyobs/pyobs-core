from __future__ import annotations

import datetime
from abc import ABCMeta
from typing import Any, Self, TypeVar

from astroplan import Observer
from pydantic import BaseModel as PydanticBaseModel
from pydantic import ConfigDict, PrivateAttr, model_serializer, model_validator
from pydantic_core.core_schema import ValidationInfo, ValidatorFunctionWrapHandler

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

    @model_serializer(mode="wrap")
    def inject_class_on_serialization(self, handler: ValidatorFunctionWrapHandler) -> dict[str, Any]:
        # Collect fields from the concrete runtime type to avoid Pydantic v2
        # resolving field schemas against the abstract base type when nested in a parent model
        result = {field_name: getattr(self, field_name) for field_name in type(self).model_fields}
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
                return klass.model_validate(modified_value, context=info.context)
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
