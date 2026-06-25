from __future__ import annotations

import inspect
import logging
from typing import TYPE_CHECKING, get_type_hints

from pydantic import Field, ValidationError, create_model, model_validator

from pyobs.object import get_class_from_string

if TYPE_CHECKING:
    from pyobs.robotic.task import TaskData
from pyobs.robotic.scripts import Script

log = logging.getLogger(__name__)


def _get_valid_param_names(method) -> set[str]:
    return {name for name in inspect.signature(method).parameters if name not in ("self", "kwargs")}


def _build_params_model(method, provided_keys):
    sig = inspect.signature(method)
    hints = get_type_hints(method, include_extras=True)
    fields = {}

    for name, param in sig.parameters.items():
        if name not in provided_keys:
            continue

        annotation = hints.get(name, param.annotation)
        default = ... if param.default is inspect.Parameter.empty else param.default
        fields[name] = (annotation, default)

    return create_model(
        f"{method.__qualname__.replace('.', '_')}_Params",
        **fields,
    )


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

        method = getattr(cls, self.method)
        valid_names = _get_valid_param_names(method)

        for key in self.params:
            if key not in valid_names:
                raise ValueError(f"Unknown parameter '{key}'")

        if self.params:
            try:
                ParamsModel = _build_params_model(method, set(self.params.keys()))
                ParamsModel.model_validate(self.params)
            except ValidationError as e:
                raise ValueError(str(e))

        return self

    async def can_run(self, data: TaskData | None) -> bool:
        cls = get_class_from_string(self.interface)
        if not await self.comm.has_proxy(self.module, cls):
            self._cant_run_reason = f"Module {self.module} not found."
            return False
        self._cant_run_reason = None
        return True

    async def run(self, data: TaskData | None) -> None:
        cls = get_class_from_string(self.interface)
        async with self.comm.proxy(self.module, cls) as proxy:
            await proxy.execute(self.method, **self.params)


__all__ = ["CallModuleScript"]
