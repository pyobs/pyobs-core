# Plan: `max_age` parameter for `get_state()` / `wait_for_state()`

Status: proposed

## Problem

Every stateful interface's `State` dataclass carries a `time: Time = field(default_factory=Time.now)`
field, stamped when the publishing module constructs the object (e.g. `WeatherState.time`,
`pyobs/interfaces/IWeather.py:25`; `TemperaturesState.time`, `pyobs/interfaces/ITemperatures.py:20`).
Confirmed via the interface registry that **all 33** interfaces with `has_own_state() == True`
have this field — there is no exception to design around.

Despite that, nothing in `pyobs-core` ever reads `.time`. `Proxy.get_state()`
(`pyobs/comm/proxy.py:175-177`) and `Proxy.wait_for_state()` (`pyobs/comm/proxy.py:193-223`) return
whatever's cached with no age check, and every consumer site in the codebase (`mixins/follow.py`,
`mixins/waitformotion.py`, `modules/focus/focusmodel.py`, `modules/focus/focusseries.py`,
`modules/pointing/acquisition.py`, `modules/pointing/autoguiding.py`,
`utils/offsets/applyoffsets.py`, `utils/offsets/applyaltazoffsets.py`,
`robotic/scripts/**`, `mixins/weatheraware.py`) uses the returned state immediately, unconditionally.

The concrete case this matters for: `WeatherAwareMixin.__weather_check()`
(`pyobs/mixins/weatheraware.py:105-142`) polls `proxy.wait_for_state(IWeather, timeout=5.0)` every
10s and trusts `weather_state.good` (`weatheraware.py:125`) as soon as it gets a non-`None` result.
`wait_for_state()` returns the cached value immediately if one already exists
(`proxy.py:205-206`) — it does not distinguish "just arrived" from "cached from three hours ago."
If the remote `Weather` module's background update loop (`pyobs/modules/weather/weather.py:118-130`,
`_run` → `_loop` → `_update`) silently stops ticking — an unhandled exception inside `_update()`
outside its own `try/except`, a hung `WeatherApi` call, anything — while the XMPP connection and
pubsub subscription stay up, `WeatherAwareMixin` keeps treating the last published `good=True` as
current indefinitely. This is the one place in `pyobs-core` where stale state has a physical
consequence (a dome/roof left open in bad weather because nothing noticed the feed had died).

There's also a transport-level way for the same symptom to occur even when `Weather`'s update loop
is healthy: the ejabberd shaper incident (#664/#666) found that a connection can look fully alive
(TCP `ESTABLISHED`, no error) while ejabberd's per-connection shaper throttles outbound bytes/sec
and queues stanzas — observed delays of minutes, once ~24 minutes, before a stanza got through. A
`publish` IQ for a fresh `WeatherState` could sit shaped on the wire for that long, so "the pubsub
subscription stays up" is not sufficient evidence that state is current — reinforcing that a
freshness check needs to be based on the state's own timestamp (see Implementation §1), not on
connection liveness.

A second, distinct transport effect points the same way: separate throughput testing (headline
number recovered, original test run itself unrecoverable — see
`ejabberd-throughput-benchmarking.md`) found simultaneous state pushes taking roughly **15x longer**
than the same pushes done sequentially — plausibly the same shaper mechanism (a burst of concurrent
publishes exhausts the per-connection burst allowance immediately, where sequential publishes might
not), but not yet confirmed as the specific cause. Unlike the single delayed-IQ case, this one
scales with how many modules in a fleet happen to publish state at once, which is exactly the
"10-100 agents" regime `pyobs_2_0_wire_protocol.md` assumes is fine without measurement — so
staleness risk from this mechanism is a fleet-size question, not just a per-module one.

## Decision

Add an optional `max_age: float | None = None` keyword parameter to both `get_state()` and
`wait_for_state()`. When given, a cached state older than `max_age` seconds is treated the same
as "not yet published" by that method's existing contract — `None` for `get_state()`, and for
`wait_for_state()` the same "wait for the next update, `None` on timeout" path already used for
the no-cache-yet case. No new return type, no new exception type — callers that don't pass
`max_age` see no behavior change at all.

Rejected: a mandatory/global default `max_age` (e.g. baked into `wait_for_state`'s existing
`timeout: float = 10.0` default). Staleness tolerance is interface-specific — weather needs
freshness within roughly a minute, but `IFocuser`/`ICooling` setpoint state doesn't go "stale" in
the same sense at all (it's still true until changed, not a periodically-refreshed reading). A
global default would either be meaningless for most interfaces or need a per-interface override
table, which is more machinery than the actual problem (one unsafe consumer) warrants. Making it
opt-in per call site keeps the fix scoped to where staleness is actually a correctness concern.

## Implementation

### 1. `Proxy` — the actual freshness check

**File:** `pyobs/comm/proxy.py`

Add a small helper and thread `max_age` through both methods:

```python
def _state_age(self, state: Any) -> float:
    """Seconds since `state` (a State dataclass instance) was constructed by its publisher."""
    t = getattr(state, "time", None)
    if t is None:
        raise ValueError(
            f"{type(state).__name__} has no 'time' field -- max_age is not supported for this interface."
        )
    return (Time.now() - t).sec

def get_state(self, interface: type[Interface], *, max_age: float | None = None) -> Any | None:
    """Latest known state for the given interface, or None if nothing has arrived yet
    (or, with max_age given, if the latest known state is older than max_age seconds)."""
    state = self._state.get(interface)
    if state is None or max_age is None:
        return state
    return state if self._state_age(state) <= max_age else None

async def wait_for_state(
    self,
    interface: type[Interface],
    timeout: float = 10.0,
    *,
    max_age: float | None = None,
) -> Any:
    """Return state immediately if available (and fresh enough per max_age), otherwise wait
    for the next update. Returns None on timeout, same as today."""
    cached = self._state.get(interface)
    if cached is not None and (max_age is None or self._state_age(cached) <= max_age):
        return cached

    event = asyncio.Event()

    def _notify(state: Any) -> None:
        self._state[interface] = state
        event.set()

    await self._comm.subscribe_state(self._client, interface, _notify)
    try:
        await asyncio.wait_for(event.wait(), timeout=timeout)
    except TimeoutError:
        pass
    finally:
        await self._comm.unsubscribe_state(self._client, interface, _notify)

    result = self._state.get(interface)
    if max_age is not None and result is not None and self._state_age(result) > max_age:
        return None
    return result
```

Needs `from pyobs.utils.time import Time` added to `proxy.py`'s imports.

Note the `wait_for_state` re-check after the wait: if `max_age` is set and the value that arrives
(or was already there) is still stale by the time we look — e.g. a delayed/replayed update, or a
fresh one that's already aged past `max_age` by the time the caller inspects it — the method
returns `None` rather than a value that's nominally "new" but still fails the caller's freshness
bar. This is a best-effort check (there is an inherent TOCTOU gap between the check and the
caller's use of the value, same as any freshness check over an async channel), not a guarantee.

### 2. `Interface.get_state()` / `Interface.wait_for_state()` — matching stub signatures

**File:** `pyobs/interfaces/interface.py:44-53`

```python
def get_state(self, interface: "type[Interface]", *, max_age: float | None = None) -> Any | None:
    """Return the last received state for the given interface, or None."""
    return None

async def wait_for_state(
    self, interface: "type[Interface]", timeout: float = 10.0, *, max_age: float | None = None
) -> Any | None:
    """Return state immediately if available, otherwise wait for the first update."""
    return None
```

These stubs are never actually reached at runtime for a real `Proxy` — `Proxy.__init__`
(`proxy.py:56-57`) dynamically rebuilds `self.__class__` as `type("Proxy", tuple([cls] +
interfaces), {})`, putting `Proxy` ahead of the mixed-in `Interface` subclasses in MRO, so
`Proxy`'s own methods always win. They exist purely so a typed reference (e.g. a variable typed as
`IWeather` obtained through `module.proxy(name, IWeather)`) type-checks the `max_age` keyword under
`pyrefly` — kept in sync with step 1's signature so that doesn't drift.

### 3. Fix the concrete unsafe consumer: `WeatherAwareMixin`

**File:** `pyobs/mixins/weatheraware.py`

Add a constructor parameter and pass it through the existing poll call:

```python
def __init__(self, weather: str | IWeather | None = None, weather_max_age: float = 120.0, **kwargs: Any):
    self.__weather = weather
    self.__weather_max_age = weather_max_age
    ...
```

```python
weather_state = await proxy.wait_for_state(IWeather, timeout=5.0, max_age=self.__weather_max_age)
```

`120.0` (seconds) as the default: `Weather._loop()` (`pyobs/modules/weather/weather.py:122-130`)
re-publishes every 5s on a successful poll or every 60s after a failed one, so 120s is roughly 2x
the worst normal inter-publish gap — loose enough not to false-positive on a single slow tick,
tight enough to catch a genuinely dead update loop within a couple of `__weather_check` cycles
(which itself polls every 10s, `weatheraware.py:142`). This is a judgment call, not a derived
constant — flagged here so it can be revisited against real deployment behavior rather than
treated as load-bearing.

This default is sized against the *application* failure mode (dead update loop), not the
*transport* one from the shaper incident noted above. A shaper-throttled connection delaying a
publish by minutes will correctly make `wait_for_state` report `None` past 120s — that's the
fail-safe behavior working as intended, not a false positive, since a delayed reading really is
stale by the time the caller would act on it. But it does mean `weather_max_age=120.0` will trip
during ordinary shaper contention on a deployment like pyobs-iagvt's (pre-fix: unbounded delay,
post-fix: still shaped, just no longer an unbounded hang), which is a legitimate-but-currently-
unquantified false-positive rate this plan doesn't yet have data for. `ejabberd-throughput-
benchmarking.md` (headline ~15x ratio known, absolute latencies not) would be the place to get an
actual publish-latency distribution under shaper load before treating 120s as tuned rather than
guessed.

With `weather_state` now `None` both when the module hasn't published yet *and* when its last
publish is too old, no other change is needed in `__weather_check()` — line 125's existing
`this.__is_weather_good = weather_state.good if weather_state is not None else False` already
treats "no usable state" as bad weather (fail-safe), which is exactly the right behavior for a
stale feed too.

## Consequences

- **Good:** Closes the concrete gap found — a dead `Weather` update loop now degrades to "bad
  weather" (parks/closes) within roughly a couple of poll cycles instead of trusting arbitrarily
  old cached data forever.
- **Good:** Fully opt-in and backward compatible — every existing `get_state()`/`wait_for_state()`
  call site (all the ones enumerated in Problem) keeps its current behavior unchanged.
- **Good:** No new interface/wire changes — `time` is already published today; this only adds a
  consumer-side check.
- **Neutral:** Only `WeatherAwareMixin` is updated to use `max_age` as part of this plan. Other
  consumer sites (`follow.py`, `acquisition.py`'s offset/pointing reads, `focusmodel.py`'s
  temperature read, etc.) are left as-is — none of them were found to have the same "silently
  trusts arbitrarily old data with a safety consequence" shape that `WeatherAwareMixin` has, and
  adding `max_age` to them speculatively isn't part of this plan. Worth a follow-up look if a
  similar concrete case turns up.
- **Neutral:** `max_age` assumes the interface's `State` dataclass has a `.time` field. True for
  all 33 stateful interfaces today (verified against the registry, not by convention alone), and
  `_state_age()` raises `ValueError` immediately if a future interface breaks that — a clear
  failure at the call site rather than `max_age` silently doing nothing.
