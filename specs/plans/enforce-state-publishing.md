# Plan: Enforce state publishing for stateful interfaces

Status: proposed

## Problem

Modules can declare they implement an interface with `has_own_state() == True` (e.g.
`ICooling`, `IExposure`, `IRunning`) but never call `self.comm.set_state(Interface, ...)` to
publish that state. Subscribers wait forever for state that never arrives — the proxy's
`wait_for_state()` times out silently, and the module's state is permanently missing from
clients.

Today all concrete modules in `pyobs-core` happen to publish state correctly, but there is
no mechanism to prevent regressions when new modules are added or existing ones are modified.

## Considered options

1. **Track published state in `Comm` + validate in `Module.startup()`** — Add a
   `_published_state` set to `Comm`, populated by `set_state()`. After `open()` completes in
   `startup()`, check that every interface with `has_own_state()` has been published. Log a
   warning for missing state.

2. **Abstract method on stateful interfaces** — Require interfaces with `state` to declare an
   `async def initial_state()` method that modules must implement. The base `Module.open()`
   calls it automatically.

3. **Test-only enforcement** — Add a parametrized pytest that instantiates each concrete module
   (with `DummyComm`) and verifies all stateful interfaces have published state after `open()`.

## Decision

Option 1 (runtime tracking + startup warning), supplemented by option 3 (test coverage).

Option 2 was rejected because: (a) it requires every stateful interface to add a new abstract
method, which is a large interface change; (b) some state is genuinely dynamic (weather
readings, temperature sensors) and can't be known at open time; (c) it conflates "must publish
state" with "must know initial values at open time."

A hard error in `startup()` was rejected because some modules publish state from background
tasks (e.g. `Weather._update()`, `DummyCamera._cooling_thread()`). A warning is the right
level — it catches the common case (module forgot to publish in `open()`) without breaking
modules that intentionally delay.

## Implementation

### 1. `Comm` — track published state

**File:** `pyobs/comm/comm.py`

Add to `__init__()`:
```python
self._published_state: set[type[Interface]] = set()
```

In `set_state()`, record the interface before delegating:
```python
async def set_state(self, interface: type[Interface], state: Any) -> None:
    self._published_state.add(interface)
    await self._set_state(interface, state)
```

Add a check method:
```python
def missing_published_state(self, interfaces: list[type[Interface]]) -> list[type[Interface]]:
    """Return interfaces that have has_own_state() but haven't had set_state() called."""
    return [i for i in interfaces if i.has_own_state() and i not in self._published_state]
```

### 2. `Module.startup()` — warn on missing state

**File:** `pyobs/modules/module.py`

After `open()` returns, before `set_state(READY)`:

```python
async def startup(self) -> None:
    await self.open()

    # warn if any stateful interface hasn't published state yet
    if self._comm is not None:
        missing = self._comm.missing_published_state(self._interfaces)
        for iface in missing:
            log.warning(
                "Module %s implements %s which declares state, "
                "but no state has been published for it yet.",
                self.name,
                iface.__name__,
            )

    await self.set_state(ModuleState.READY)
```

### 3. Test — parametrized check for all concrete modules

**File:** `tests/modules/test_module_state_publishing.py` (new)

A parametrized test that:
1. Discovers all concrete `Module` subclasses in `pyobs.modules`
2. Instantiates each with a `DummyComm`
3. Runs `open()` (not `startup()`, to avoid needing a full comm setup)
4. Checks that `comm.missing_published_state(module.interfaces)` is empty
5. Skips modules that require external dependencies (config files, hardware)

This catches the regression case: someone adds `ICooling` to a module but forgets to call
`comm.set_state(ICooling, ...)` in `open()`.

### 4. `DummyComm` — no changes needed

`DummyComm` inherits from `Comm`, so it gets `_published_state` and `missing_published_state`
automatically. `DummyComm` doesn't implement `_set_state()` (it's a no-op), but
`set_state()` still records the interface in `_published_state` before delegating — which is
exactly what the test needs.

## Consequences

- **Good:** Catches the most common form of the bug (forgetting to publish state in `open()`).
- **Good:** Non-breaking — existing modules all publish state, so no warnings in practice.
- **Good:** The warning message names the specific interface, making it easy to fix.
- **Neutral:** Modules that publish state from background tasks (Weather, DummyCamera cooling)
  will still show a warning during the gap between `open()` and the first background tick.
  This is acceptable — it surfaces the timing rather than hiding it.
- **Neutral:** External modules (outside `pyobs-core`) get the same runtime behavior but not
  the test. The test is a development aid, not a runtime guard.
