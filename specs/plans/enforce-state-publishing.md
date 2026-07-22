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

Option 1 (runtime tracking + startup warning), supplemented by option 3 (test coverage), plus
a convention: **every module publishes an initial (possibly placeholder) value for each of its
stateful interfaces synchronously in `open()`**, even when the "real" value is only known later.

This is not a new convention — `_dummytelescopebase.py` already does it (`open()` publishes
`IFocuser`/`IFilters`/`IPointingRaDec`/etc. with current-but-not-yet-meaningful values), and
`dummysolartelescope.py:58-60` states the rationale explicitly in a comment: *"publish the disk
centre as a placeholder so the pubsub nodes exist (real values get set once a move_* call comes
in)"*. `DummyCamera.open()` does the same for `ICooling`. The one module in `pyobs-core` that
doesn't follow it is `Weather`: `IWeather` is currently only published from `_update()`, which
runs on `Weather`'s background task and hasn't had its first event-loop turn by the time
`startup()`'s post-`open()` check would run — so implementing option 1 as originally written
would make `Weather` warn (and fail the option-3 test) on every single startup, despite `Weather`
not actually being buggy. **Fix:** extract `Weather`'s two-line publish
(`comm.set_state(IWeather, WeatherState(good=is_good, readings=self._get_readings()))`) into a
small `_publish_state()` helper (mirroring `MockWeather`, which already does this) and call it
once from `open()` in addition to `_update()`. `WeatherStatus.__init__` already defaults to
`{"good": False}` and `_get_readings()` already tolerates an empty sensor dict, so this requires
no change to `Weather`'s internal state handling — `good=False` ("unknown weather is bad") is
also the correct fail-safe placeholder.

With this convention in place, "has every stateful interface been published by the end of
`open()`" becomes a true invariant with no timing-dependent exceptions, which is what makes a
synchronous, non-flaky check (both the runtime warning and the option-3 test) viable in the
first place.

Option 2 was rejected because: (a) it requires every stateful interface to add a new abstract
method, which is a large interface change; (b) some state is genuinely dynamic (weather
readings, temperature sensors) and can't be known at open time; (c) it conflates "must publish
state" with "must know initial values at open time." (The placeholder convention above solves
the same problem without a new abstract method — modules keep publishing dynamic updates from
background tasks as they already do, they just also publish a first cut synchronously.)

A hard error in `startup()` was rejected in favor of a warning regardless — even with the
placeholder convention adopted, a hard error is more blast radius than this check needs (an
`open()` override that's still mid-refactor, a third-party module updated more slowly than
`pyobs-core`, etc. shouldn't hard-crash startup over a state-publishing gap). A warning catches
the regression just as visibly in logs without that risk.

An alternative considered and rejected: instead of requiring a synchronous placeholder, delay
the check itself (e.g. warn ~10s after `open()` instead of immediately) to give background
tasks a chance to tick once. Rejected because: (a) it's still racy — `Weather`'s own loop sleeps
5-60s depending on success/failure, so a fixed delay isn't guaranteed to catch the first tick
either; (b) it turns a synchronous, deterministic check into a scheduled task with its own
lifecycle (must be cancelled on `close()`); (c) it doesn't help the option-3 test, which can't
`await asyncio.sleep(10)` per module without making the suite slow and flaky.

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

### 3. `Weather` — publish a placeholder synchronously in `open()`

**File:** `pyobs/modules/weather/weather.py`

Extract the publish call already at the end of `_update()` into a `_publish_state()` helper
(mirroring `MockWeather._publish_state()`, which already follows this pattern), and call it once
from `open()` as well as from `_update()`:

```python
async def open(self) -> None:
    """Open module."""
    await Module.open(self)

    if self._comm:
        await self.comm.register_event(BadWeatherEvent)
        await self.comm.register_event(GoodWeatherEvent)

    await self.comm.set_state(IRunning, RunningState(running=self._active))
    await self._publish_state()

async def _publish_state(self) -> None:
    is_good = True if not self._active else self._weather.is_good
    await self.comm.set_state(IWeather, WeatherState(good=is_good, readings=self._get_readings()))
```

`_update()`'s trailing publish becomes a call to `self._publish_state()`. No change to
`WeatherStatus` is needed — it already defaults to `{"good": False}` and `_get_readings()`
already tolerates an empty sensor dict, so the `open()`-time call publishes `good=False,
readings=[]`, a correct fail-safe placeholder ("unknown weather is bad").

### 4. Test — parametrized check for all concrete modules

**File:** `tests/modules/test_module_state_publishing.py` (new)

A parametrized test that:
1. Discovers all concrete `Module` subclasses in `pyobs.modules`
2. Instantiates each with a `DummyComm`
3. Runs `open()` (not `startup()`, to avoid needing a full comm setup)
4. Checks that `comm.missing_published_state(module.interfaces)` is empty
5. Skips modules that require external dependencies (config files, hardware) to construct/open

With step 3's `Weather` fix, this is a real invariant — no module in `pyobs-core` needs a
timing-based exemption. Modules skipped by point 5 are skipped because they can't be
instantiated/opened at all in a unit test (real hardware, external services), not because of
state-publishing timing.

This catches the regression case: someone adds `ICooling` to a module but forgets to call
`comm.set_state(ICooling, ...)` in `open()`.

### 5. `DummyComm` — no changes needed

`DummyComm` inherits from `Comm`, so it gets `_published_state` and `missing_published_state`
automatically. `DummyComm` doesn't implement `_set_state()` (it's a no-op), but
`set_state()` still records the interface in `_published_state` before delegating — which is
exactly what the test needs.

## Consequences

- **Good:** Catches the most common form of the bug (forgetting to publish state in `open()`).
- **Good:** Non-breaking once `Weather` is updated per step 3 — every module publishes all its
  stateful interfaces by the end of `open()`, so there are no warnings in practice and no
  timing-based exceptions to document or maintain.
- **Good:** The warning message names the specific interface, making it easy to fix.
- **Good:** Reinforces an existing convention (`_dummytelescopebase.py`'s placeholder-state
  pattern) instead of introducing a second, competing one.
- **Neutral:** Modules must remember to publish a placeholder in `open()` even for interfaces
  whose real value is only known later (dynamic sensor readings, tracking targets, etc.) — this
  is already the norm for telescope/camera modules; `Weather` is the only one being brought in
  line with it.
- **Neutral:** External modules (outside `pyobs-core`) get the same runtime behavior but not
  the test. The test is a development aid, not a runtime guard.
