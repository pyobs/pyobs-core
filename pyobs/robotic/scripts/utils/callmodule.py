from __future__ import annotations

import inspect
import logging
from typing import TYPE_CHECKING, Any

from pydantic import Field, model_validator

from pyobs.object import get_class_from_string

if TYPE_CHECKING:
    from pyobs.robotic.task import TaskData
from pyobs.robotic.scripts import Script

log = logging.getLogger(__name__)


class CallModuleScript(Script):
    """Script for calling a method on a module."""

    module: str
    interface: str
    method: str
    params: dict[str, str | int | float] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _validate_params(self) -> CallModuleScript:
        cls = get_class_from_string(self.interface)
        if not hasattr(cls, self.method):
            raise ValueError(f"Method '{self.method}' not found on {self.interface}")

        sig = inspect.signature(getattr(cls, self.method))
        valid_params = {name: param for name, param in sig.parameters.items() if name not in ("self", "kwargs")}

        for name, value in self.params.items():
            if name not in valid_params:
                raise ValueError(f"Unknown parameter '{name}' for {self.interface}.{self.method}")
            annotation = valid_params[name].annotation
            if annotation is not inspect.Parameter.empty and annotation is not Any:
                origin = getattr(annotation, "__origin__", None)
                args = getattr(annotation, "__args__", ())
                if origin is type(None):
                    continue
                types = tuple(a for a in args if a is not type(None)) if args else (annotation,)
                if not isinstance(value, types):
                    raise ValueError(f"Parameter '{name}' should be {annotation}, got {type(value).__name__}")

        return self

    async def can_run(self, data: TaskData | None) -> bool:
        try:
            cls = get_class_from_string(self.interface)
            await self.comm.proxy(self.module, cls)
            self._cant_run_reason = None
            return True
        except ValueError:
            self._cant_run_reason = f"Module {self.module} not found."
            return False

    async def run(self, data: TaskData | None) -> None:
        cls = get_class_from_string(self.interface)
        proxy = await self.comm.proxy(self.module, cls)
        await proxy.execute(self.method, **self.params)


__all__ = ["CallModuleScript"]
