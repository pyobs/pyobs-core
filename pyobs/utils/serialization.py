from __future__ import annotations
from abc import ABCMeta
from typing import Any
from pydantic import BaseModel, model_serializer, model_validator
from pydantic_core.core_schema import ValidatorFunctionWrapHandler

from pyobs.object import get_class_from_string


class SubClassBaseModel(BaseModel, metaclass=ABCMeta):
    """Pydantic base model for pyobs sub classes that need to be serialized."""

    @model_serializer(mode="wrap")
    def inject_class_on_serialization(self, handler: ValidatorFunctionWrapHandler) -> dict[str, Any]:
        result: dict[str, Any] = handler(self)
        if "class" in result:
            raise ValueError('Cannot use field "type". It is reserved.')
        result["class"] = f"{self.__module__}.{self.__class__.__name__}"
        return result

    @model_validator(mode="wrap")  # noqa  # the decorator position is correct
    @classmethod
    def retrieve_class_on_deserialization(cls, value: Any, handler: ValidatorFunctionWrapHandler) -> Any:
        if isinstance(value, dict):
            # WARNING: we do not want to modify `value` which will come from the outer scope
            # WARNING2: `sub_cls(**modified_value)` will trigger a recursion, and thus we need to remove `class`
            modified_value = value.copy()
            sub_cls_name = modified_value.pop("class", None)
            if sub_cls_name is not None:
                klass = get_class_from_string(sub_cls_name)
                return klass(**modified_value)
        return handler(value)


__all__ = ["SubClassBaseModel"]
