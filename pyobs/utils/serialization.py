from __future__ import annotations

import datetime
from abc import ABCMeta
from typing import Any, TypeVar

from astropy.coordinates import EarthLocation
from pydantic import BaseModel as PydanticBaseModel, model_serializer, model_validator, ConfigDict, PrivateAttr
from pydantic_core.core_schema import ValidatorFunctionWrapHandler
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

    def __init__(self, **kwargs: Any) -> None:
        PydanticBaseModel.__init__(self, **kwargs)
        # Object.__init__(self)


class SubClassBaseModel(BaseModel, metaclass=ABCMeta):
    """Pydantic base model for pyobs sub classes that need to be serialized."""

    @model_serializer(mode="wrap")
    def inject_class_on_serialization(self, handler: ValidatorFunctionWrapHandler) -> dict[str, Any]:
        result = handler(self)
        result["class"] = f"{self.__module__}.{self.__class__.__name__}"
        return result

    @model_validator(mode="wrap")  # noqa  # the decorator position is correct
    @classmethod
    def retrieve_class_on_deserialization(cls, value: Any, handler: ValidatorFunctionWrapHandler) -> Any:
        if isinstance(value, dict):
            from pyobs.object import get_class_from_string

            # WARNING: we do not want to modify `value` which will come from the outer scope
            # WARNING2: `sub_cls(**modified_value)` will trigger a recursion, and thus we need to remove `class`
            modified_value = value.copy()
            sub_cls_name = modified_value.pop("class", None)
            if sub_cls_name is not None:
                klass = get_class_from_string(sub_cls_name)
                return klass(**modified_value)
        return handler(value)


__all__ = ["BaseModel", "SubClassBaseModel"]
