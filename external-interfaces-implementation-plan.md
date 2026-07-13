# External Interfaces Registry: Implementation Plan

## Overview

Replace two hardcoded `pyobs.interfaces` namespace lookups with a module-level registry populated via `__init_subclass__`, so external packages can define their own interfaces that resolve correctly over the wire.

---

## Phase 1: Registry in `pyobs/interfaces/interface.py`

### 1.1 Add `_REGISTRY` dict and `__init_subclass__` hook

```python
from abc import ABCMeta
from typing import Any, ClassVar

_REGISTRY: dict[str, type["Interface"]] = {}


class Interface(metaclass=ABCMeta):
    """Base class for all interfaces in pyobs."""

    version: int = 1
    state: ClassVar[type | None] = None
    capabilities: ClassVar[type | None] = None

    __module__ = "pyobs.interfaces"

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        existing = _REGISTRY.get(cls.__name__)
        if existing is not None and existing is not cls:
            raise TypeError(
                f"Interface name '{cls.__name__}' is already registered by "
                f"{existing.__module__}.{existing.__qualname__}; "
                f"choose a distinct name for {cls.__module__}.{cls.__qualname__}."
            )
        _REGISTRY[cls.__name__] = cls

    # ... existing methods unchanged ...
```

The `existing is not cls` check handles re-imports of the same module (same class object, no error) while catching genuinely different classes with the same name (raises `TypeError` immediately at import time).

### 1.2 Add lookup functions

```python
def get_registered_interface(name: str) -> type["Interface"] | None:
    """Look up a registered interface class by name, or None if unknown."""
    return _REGISTRY.get(name)


def registered_interfaces() -> dict[str, type["Interface"]]:
    """All currently-registered interface classes, keyed by name."""
    return dict(_REGISTRY)
```

### 1.3 Update `__all__`

```python
__all__ = ["Interface", "get_registered_interface", "registered_interfaces"]
```

---

## Phase 2: Update Chokepoint — `XmppComm`

File: `pyobs/comm/xmpp/xmppcomm.py`

### 2.1 `_get_interfaces()` (~line 409)

Replace:

```python
local_cls = getattr(pyobs.interfaces, name, None)
```

With:

```python
from pyobs.interfaces.interface import get_registered_interface
local_cls = get_registered_interface(name)
```

No other changes in this method — version matching (`str(local_cls.version) == version`) and the `issubclass(local_cls, Interface)` check remain unchanged.

---

## Phase 3: Update Chokepoint — `Comm._interface_names_to_classes`

File: `pyobs/comm/comm.py`

### 3.1 `_interface_names_to_classes()` (lines 330–363)

Replace the entire method body:

```python
@staticmethod
def _interface_names_to_classes(interfaces: list[str]) -> list[type[Interface]]:
    """Converts a list of interface names to interface classes."""
    interface_classes = []
    for interface_name in interfaces:
        cls = get_registered_interface(interface_name)
        if cls is not None:
            interface_classes.append(cls)
        else:
            log.error('Could not find interface "%s" for client.', interface_name)
    return interface_classes
```

### 3.2 Update import

Add to imports at top of file:

```python
from pyobs.interfaces.interface import get_registered_interface
```

The existing `import pyobs.interfaces` and `from pyobs.interfaces import Interface` can remain (used elsewhere in the file, e.g., `_event_names_to_classes` at line 427).

---

## Phase 4: No Changes Needed

The following require **no modifications**:

- `pyobs/interfaces/__init__.py` — keeps re-exporting core interfaces; resolution no longer depends on this module's namespace
- `pyobs/comm/local/localcomm.py` — same-process, uses live class objects directly, never touches string-based resolution
- `pyobs/comm/dummy/dummycomm.py` — same as LocalComm
- disco#info wire format (`urn:pyobs:interface:{name}:{version}`) — unchanged
- Version matching, RPC dispatch, capabilities/state pub-sub — already interface-agnostic

---

## Files Changed Summary

| File | Action |
|---|---|
| `pyobs/interfaces/interface.py` | Add `_REGISTRY`, `__init_subclass__`, `get_registered_interface`, `registered_interfaces`, update `__all__` |
| `pyobs/comm/xmpp/xmppcomm.py` | Replace `getattr(pyobs.interfaces, name, None)` with `get_registered_interface(name)` |
| `pyobs/comm/comm.py` | Replace `inspect.getmembers` scan + inner loop with registry lookup |

---

## Testing Checklist

1. Two distinct classes named `IFoo` in different modules: importing both raises `TypeError` on the second import, naming both offending modules.
2. Re-importing the same interface module twice (same class object) does **not** raise.
3. An external interface round-trips: module A implements it and advertises it via disco#info, module B builds a proxy and successfully calls a method.
4. Existing core interface resolution (`ICamera`, `ITelescope`, etc.) continues to work unchanged.
5. Version-mismatch diagnostics (`_diagnose_missing_interface` near `xmppcomm.py:425`) still fire correctly for registered external interfaces.

---

## Notes

- `inspect` import in `comm.py` must stay — also used at line 427 for `_event_names_to_classes`
- `LocalComm` and `DummyComm` never had the gap; any class object works identically once you're in the same process
- The registry closes a gap in the wire protocol `XmppComm` uses only
