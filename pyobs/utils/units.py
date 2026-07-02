from __future__ import annotations

import functools
import inspect
from typing import Annotated, Any, get_args, get_origin, get_type_hints

from .enums import Unit


def _extract_unit(hint: Any) -> Unit | None:
    if get_origin(hint) is Annotated:
        for arg in get_args(hint)[1:]:
            if isinstance(arg, Unit):
                return arg
    return None


def _interface_unit_hints(cls: type, method_name: str) -> dict[str, Unit]:
    """Return Unit annotations from the abstract interface declaration for method_name."""
    for base in cls.__mro__:
        member = base.__dict__.get(method_name)
        if member is not None and getattr(member, "__isabstractmethod__", False):
            hints = get_type_hints(member, include_extras=True)
            return {name: u for name, hint in hints.items() if (u := _extract_unit(hint)) is not None}
    return {}


def with_units(func: Any) -> Any:
    """Convert annotated float parameters to astropy Quantities before the method runs.

    Reads Unit annotations from the abstract interface declaration so concrete
    implementations don't need to repeat them.
    """

    @functools.wraps(func)
    async def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        units = _interface_unit_hints(type(self), func.__name__)
        bound = inspect.signature(func).bind(self, *args, **kwargs)
        bound.apply_defaults()
        for name, unit in units.items():
            if name in bound.arguments:
                bound.arguments[name] = bound.arguments[name] * unit.to_astropy()
        return await func(*bound.args, **bound.kwargs)

    return wrapper


__all__ = ["with_units"]
