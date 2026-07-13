# Externally-defined interfaces: registry design

## Status

Speculative — no concrete external interface exists yet (this was explored
alongside `pyobs-polaris`'s need for `IConfig`-like functionality, which
ended up solved differently via `IStructuredConfig`; see
`IStructuredConfig-spec.md`). This doc is a ready-to-implement design to
reach for if/when an external package genuinely needs to define its own
interface. Not urgent, no timeline.

Repo: `pyobs-core`. All paths below relative to repo root.

## Problem

`Interface` (`pyobs/interfaces/interface.py`) is a plain ABC — nothing
technically stops an external package from subclassing it. Publishing
already works generically: disco#info features are built from
`self._module.interfaces` with no restriction to core
(`pyobs/comm/xmpp/xmppcomm.py:252`,
`f"urn:pyobs:interface:{i.__name__}:{i.version}"`).

**Resolution is what's broken.** Two chokepoints hardcode lookups against
the `pyobs.interfaces` module namespace specifically, so a remote module
advertising an externally-defined interface has it silently dropped on the
consuming side:

1. `pyobs/comm/xmpp/xmppcomm.py:409`, inside `_get_interfaces()`:
   ```python
   local_cls = getattr(pyobs.interfaces, name, None)
   ```
2. `pyobs/comm/comm.py:341`, inside `_interface_names_to_classes()`:
   ```python
   inspection = inspect.getmembers(pyobs.interfaces, predicate=inspect.isclass)
   ```

Both need to become registry lookups instead. Everything else (version
matching, RPC dispatch, capabilities/state pub-sub) is already
interface-agnostic and needs no changes.

## 1. Registry: `pyobs/interfaces/interface.py`

Add a module-level registry populated via `__init_subclass__`. This works
fine alongside the existing `ABCMeta` metaclass — `__init_subclass__` is a
classmethod hook, orthogonal to the metaclass. Registration happens at
class-definition time (import time), which is exactly when it needs to be
available: both the module implementing an external interface and any code
building a typed proxy for it already have to import it, same implicit
constraint core interfaces rely on today.

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

    # ... existing methods (get_state, get_capabilities, wait_for_state,
    # has_own_state) unchanged ...


def get_registered_interface(name: str) -> type["Interface"] | None:
    """Look up a registered interface class by name, or None if unknown."""
    return _REGISTRY.get(name)


def registered_interfaces() -> dict[str, type["Interface"]]:
    """All currently-registered interface classes, keyed by name."""
    return dict(_REGISTRY)


__all__ = ["Interface", "get_registered_interface", "registered_interfaces"]
```

The `existing is not cls` check matters: re-importing the same module twice
gives you the same class object (no error), but two genuinely different
classes claiming the same name raises `TypeError` immediately at import
time rather than silently letting the last-imported one win.

`pyobs/interfaces/__init__.py` keeps re-exporting core interfaces as today
(`from pyobs.interfaces import ICamera`-style ergonomics still matter), but
resolution no longer depends on that module's namespace.

## 2. Update the two chokepoints (`XmppComm` only)

Both chokepoints are XMPP-specific — string names only exist because
`XmppComm` serializes interfaces to disco#info feature strings and has to
deserialize them back into classes on the other end. `Comm._interface_names_to_classes`
(`comm.py:330`) lives on the base `Comm` class but is only ever called from
`XmppComm` (`xmppcomm.py:547`).

`LocalComm` (`pyobs/comm/local/localcomm.py`) never touches interface
*names* at all — same-process, so `get_interfaces()` (line 40) just returns
`remote_client.module.interfaces` directly, live Python class objects, no
serialization round-trip. `DummyComm` similarly has no string-based
resolution to fix. **Nothing changes in either.** This registry closes a gap
in the wire protocol `XmppComm` uses; `LocalComm`/`DummyComm` never had the
gap, since any class object — external or not — works identically once
you're in the same process.

`pyobs/comm/xmpp/xmppcomm.py`, in `_get_interfaces()` (~line 409):

```python
# before
local_cls = getattr(pyobs.interfaces, name, None)

# after
from pyobs.interfaces.interface import get_registered_interface
local_cls = get_registered_interface(name)
```

`pyobs/comm/comm.py`, in `_interface_names_to_classes()` (~lines 340-363),
collapses considerably since the registry lookup replaces the
`inspect.getmembers` scan and the inner loop:

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

No other call sites need to change — version-matching logic at
`xmppcomm.py:410` (`str(local_cls.version) == version`) is unaffected, it
just now receives `local_cls` from the registry instead of `getattr`.

## 3. Collision handling

Bare `cls.__name__` is still the registry key, so two unrelated packages
both defining e.g. `IPointingModel` will collide. Three tiers, increasing
cost — this design implements **tier 2**, and documents tier 3 as a future
escalation path rather than building it now:

1. **Convention only** — document "prefix external interface names with
   something distinctive" (`IPolarisPointingModel`, not `IPointingModel`).
   Zero mechanism, relies on external authors behaving.
2. **Fail fast at import** *(implemented above)* — a genuine collision
   raises `TypeError` immediately rather than silently resolving to
   whichever class happened to be imported last. Doesn't prevent
   collisions, but turns them into a loud, immediate error instead of a
   confusing wire-level mismatch discovered later.
3. **Fully-qualified wire names** — change the disco#info feature string
   from `i.__name__` to a `qualified_name` classmethod: bare `__name__` for
   anything whose `__module__` starts with `pyobs.interfaces` (keeps the
   core wire format unchanged, no backward-compat break), but
   `f"{cls.__module__}.{cls.__qualname__}"` for anything else. Genuinely
   collision-proof, but touches the wire format — more invasive to retrofit
   once something external actually depends on the format. **Do not build
   this speculatively.** Only reach for it if a real external interface
   shows up and a real collision risk becomes concrete, since committing to
   a wire-format change ahead of need is exactly the kind of thing that's
   annoying to undo later.

## 4. Worked example

Say `pyobs-iagvt` needs a capability with no equivalent in core: triggering
a hardware-specific alignment routine on the siderostat that has no
meaningful generalization to other telescope types. Today that would either
get shoehorned into an existing interface or bolted on as a
module-specific method invisible to the generic proxy/GUI machinery. With
the registry, it becomes a real interface, defined and owned entirely
outside `pyobs-core`.

**In `pyobs-iagvt`, a new file `pyobs_iagvt/interfaces.py`:**

```python
from dataclasses import dataclass, field
from typing import Any
from pyobs.interfaces import Interface
from pyobs.utils.time import Time


@dataclass
class AlignmentState:
    in_progress: bool
    last_completed: Time | None = None
    time: Time = field(default_factory=Time.now)


class ISiderostatAlignment(Interface):
    """Siderostat-specific alignment routine. No general equivalent —
    lives in pyobs-iagvt rather than pyobs-core."""

    state = AlignmentState

    async def start_alignment_sequence(self, **kwargs: Any) -> None:
        """Trigger the mirror alignment routine."""
        ...
```

Just by being imported, `ISiderostatAlignment.__init_subclass__` fires and
it lands in the shared `_REGISTRY` — no separate registration step, no
entry in `pyobs-core` at all.

**The siderostat module implements it normally:**

```python
from pyobs_iagvt.interfaces import ISiderostatAlignment, AlignmentState

class Siderostat(Module, ISiderostatAlignment):
    async def start_alignment_sequence(self, **kwargs: Any) -> None:
        self._publish_state(AlignmentState(in_progress=True))
        await self._run_hardware_alignment()
        self._publish_state(AlignmentState(in_progress=False, last_completed=Time.now()))
```

Over the wire, `XmppComm` advertises this exactly like any core interface —
same feature string format, no special-casing:
`urn:pyobs:interface:ISiderostatAlignment:1`.

**A consumer — e.g. a small operations script, or a future
`pyobs-iagvt`-aware panel in `pyobs-web-admin` — resolves it the same way
it would resolve `ICamera`:**

```python
from pyobs_iagvt.interfaces import ISiderostatAlignment

proxy = await comm.get_proxy("siderostat", ISiderostatAlignment)
await proxy.start_alignment_sequence()
```

The consumer has to import `pyobs_iagvt.interfaces` to reference the type —
same requirement core interfaces already impose, just no longer satisfied
by `pyobs-core` alone. If `comm.get_proxy` is called with a name string
instead of the type object anywhere in your codebase, that path also goes
through `get_registered_interface`, so it resolves correctly as long as
`pyobs_iagvt.interfaces` has been imported by that point in the process.

**Collision case, for concreteness:** if `pyobs-polaris` independently
defined its own unrelated `ISiderostatAlignment` (unlikely here, but the
general case — two packages picking the same name for different things),
whichever one imports second raises `TypeError` at import time, naming
both offending modules — not a silent wire-level mismatch discovered
later during an actual alignment call.

## Testing checklist

- Two distinct classes named `IFoo` defined in different modules: importing
  both raises `TypeError` on the second import, naming both offending
  modules in the message.
- Re-importing the same interface module twice (e.g. via two different
  import paths resolving to the same module object) does **not** raise —
  only genuinely distinct class objects collide.
- An external interface (defined outside `pyobs.interfaces`, in a throwaway
  test package) round-trips: module A implements it and advertises it via
  disco#info, module B builds a proxy for module A and successfully calls a
  method on that interface.
- Existing core interface resolution (`ICamera`, `ITelescope`, etc.)
  continues to work unchanged after the chokepoint edits — this should be
  covered by whatever existing comm/proxy tests already exercise interface
  resolution; confirm they still pass rather than assuming.
- Version-mismatch diagnostics (the existing `_diagnose_missing_interface`
  path near `xmppcomm.py:425`) still fire correctly for a registered
  external interface with a version mismatch, not just for core ones.

## Explicitly out of scope for this change

- No change to the disco#info wire format (`urn:pyobs:interface:{name}:{version}`)
  — tier 3 above stays undone unless a real need appears.
- No entry_points/packaging-based plugin discovery — registration is purely
  import-time via `__init_subclass__`, consistent with how core interfaces
  already have to be imported by any consumer today.
- No changes to capabilities/state pub-sub machinery — already
  interface-agnostic (see `Comm.get_capabilities`, keyed by
  `type[Interface]`, not by name or origin).
