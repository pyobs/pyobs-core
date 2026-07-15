from abc import ABCMeta
from typing import Any, ClassVar

_REGISTRY: dict[str, "type[Interface]"] = {}


class Interface(metaclass=ABCMeta):
    """Base class for all interfaces in pyobs."""

    version: int = 1
    state: ClassVar[type | None] = None
    capabilities: ClassVar[type | None] = None

    __module__ = "pyobs.interfaces"

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)

        # only genuine interface definitions get registered. Concrete module
        # classes (e.g. `class BaseCamera(Module, ICamera, IExposureTime,
        # IImageType)`) also transitively subclass Interface, but always mix
        # in at least one base that isn't itself an Interface subclass
        # (Module, a FITS-header mixin, ...). A base only counts as "pure"
        # if it's Interface itself or is already registered -- issubclass(
        # base, Interface) alone isn't enough, since e.g. BaseCamera
        # transitively satisfies that (via ICamera) despite mixing in
        # Module, which would let DummyCamera(BaseCamera, ...) register
        # too. Checking registry membership instead propagates purity down
        # the whole chain, since BaseCamera itself never gets registered.
        def _is_pure(base: type) -> bool:
            return base is Interface or _REGISTRY.get(base.__name__) is base

        if not all(_is_pure(base) for base in cls.__bases__):
            return

        existing = _REGISTRY.get(cls.__name__)
        if existing is not None and existing is not cls:
            raise TypeError(
                f"Interface name '{cls.__name__}' is already registered by "
                f"{existing.__module__}.{existing.__qualname__}; "
                f"choose a distinct name for {cls.__module__}.{cls.__qualname__}."
            )
        _REGISTRY[cls.__name__] = cls

    def get_state(self, interface: "type[Interface]") -> Any | None:
        """Return the last received state for the given interface, or None."""
        return None

    def get_capabilities(self, interface: "type[Interface]") -> Any | None:
        """Return the capabilities for the given interface, or None."""
        return None

    async def wait_for_state(self, interface: "type[Interface]", timeout: float = 10.0) -> Any | None:
        """Return state immediately if available, otherwise wait for the first update."""
        return None

    @classmethod
    def has_own_state(cls) -> bool:
        """True if this interface defines its own state, as opposed to merely inheriting
        one from a component interface it combines (e.g. ICamera inheriting IExposure's
        state). Modules publish state under the interface that actually defines it, so
        composite interfaces would otherwise be (wrongly) treated as publishing state too.
        """
        return "state" in cls.__dict__


def get_registered_interface(name: str) -> "type[Interface] | None":
    """Look up a registered interface class by name, or None if unknown."""
    return _REGISTRY.get(name)


def registered_interfaces() -> "dict[str, type[Interface]]":
    """All currently-registered interface classes, keyed by name."""
    return dict(_REGISTRY)


__all__ = ["Interface", "get_registered_interface", "registered_interfaces"]
