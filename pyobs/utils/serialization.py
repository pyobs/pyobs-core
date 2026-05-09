from __future__ import annotations

import copy
import datetime
from abc import ABCMeta
from typing import Any, TypeVar, overload, Literal

from astropy.coordinates import EarthLocation
from pydantic import BaseModel as PydanticBaseModel, model_serializer, model_validator, Field, ConfigDict
from pydantic_core.core_schema import ValidatorFunctionWrapHandler
from astroplan import Observer

from pyobs.comm import Comm
from pyobs.vfs import VirtualFileSystem

"""Class of an Object."""
ObjectClass = TypeVar("ObjectClass")


class BaseModel(PydanticBaseModel):
    """Pydantic base model for pyobs classes that need to be serialized."""

    timezone: datetime.tzinfo = Field(exclude=True)
    location: EarthLocation = Field(exclude=True)
    vfs: VirtualFileSystem = Field(exclude=True)
    observer: Observer = Field(exclude=True)
    comm: Comm | None = Field(exclude=True)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def pyobs_model_validate(self, cls: type[PydanticBaseModel], *args, **kwargs) -> BaseModel:
        return cls.model_validate(
            *args,
            **kwargs,
            timezone=self.timezone,
            location=self.location,
            vfs=self.vfs,
            observer=self.observer,
            comm=self.comm,
        )

    @overload
    def get_object(
        self,
        config_or_object: dict[str, Any] | ObjectClass | type[ObjectClass],
        object_class: type[ObjectClass],
        **kwargs: Any,
    ) -> ObjectClass: ...

    @overload
    def get_object(
        self,
        config_or_object: dict[str, Any],
        object_class: Literal[None],
        **kwargs: Any,
    ) -> Any: ...

    @overload
    def get_object(
        self,
        config_or_object: ObjectClass | type[ObjectClass],
        object_class: Literal[None],
        **kwargs: Any,
    ) -> ObjectClass: ...

    @overload
    def get_object(
        self,
        config_or_object: dict[str, Any] | ObjectClass | type[ObjectClass],
        object_class: type[ObjectClass] | None = None,
        **kwargs: Any,
    ) -> ObjectClass | Any: ...

    def get_object(
        self,
        config_or_object: dict[str, Any] | ObjectClass | type[ObjectClass],
        object_class: type[ObjectClass] | None = None,
        **kwargs: Any,
    ) -> ObjectClass | Any:
        """Creates object from config or returns object directly, both optionally after check of type.

        Args:
            config_or_object: A configuration dict or an object itself to create/check. If a dict with a class key
                is given, a new object is created.
            object_class: Class to check object against.

        Returns:
            (New) object (created from config) that optionally passed class check.

        Raises:
            TypeError: If the object does not match the given class.
        """
        from pyobs.object import Object

        # set parameters
        params = copy.copy(kwargs)

        # copy timezone, location, vfs, and observer, if not exists
        for p in ["timezone", "location", "vfs", "observer", "comm"]:
            if Object.config_or_object_get_param(config_or_object, p) is None:
                params[p] = getattr(self, p)

        # get it
        from pyobs.object import get_object

        return get_object(config_or_object, object_class, **params)


class SubClassBaseModel(BaseModel, metaclass=ABCMeta):
    """Pydantic base model for pyobs sub classes that need to be serialized."""

    @model_serializer(mode="wrap")
    def inject_class_on_serialization(self, handler: ValidatorFunctionWrapHandler) -> dict[str, Any]:
        # result: dict[str, Any] = handler(self)
        # TODO: why doesn't this work?
        result: dict[str, Any] = self.__dict__.copy()
        if "class" in result:
            raise ValueError('Cannot use field "class". It is reserved.')
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
