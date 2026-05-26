from __future__ import annotations

import datetime
from abc import ABCMeta
from typing import Any, TypeVar, Self

from astropy.coordinates import EarthLocation
from pydantic import BaseModel as PydanticBaseModel, model_serializer, model_validator, ConfigDict, PrivateAttr
from pydantic_core.core_schema import ValidatorFunctionWrapHandler, ValidationInfo
from astroplan import Observer

from pyobs.comm import Comm
from pyobs.object import PrivateAttrMixin
from pyobs.vfs import VirtualFileSystem

"""Class of an Object."""
ObjectClass = TypeVar("ObjectClass")


class BaseModel(PydanticBaseModel, PrivateAttrMixin):
    """Pydantic base model for pyobs classes that need to be serialized."""

    _timezone: datetime.tzinfo | None = PrivateAttr(default=None)
    _location: EarthLocation | None = PrivateAttr(default=None)
    _vfs: VirtualFileSystem | None = PrivateAttr(default=None)
    _observer: Observer | None = PrivateAttr(default=None)
    _comm: Comm | None = PrivateAttr(default=None)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @model_validator(mode="after")
    def _inject_context_into_children(self, info: ValidationInfo) -> Self:
        print("inject", self.__class__.__name__)
        if info.context is not None:
            print("observer:", info.context.get("observer"))
            self._comm = info.context.get("comm")
            self._observer = info.context.get("observer")
            self._vfs = info.context.get("vfs")
            self._timezone = info.context.get("timezone")
            self._location = info.context.get("location")
        return self


class PolymorphicBaseModel(BaseModel, metaclass=ABCMeta):
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


__all__ = ["BaseModel", "PolymorphicBaseModel"]
