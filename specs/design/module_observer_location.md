# Module observer-location capabilities

Status: implemented, closed. Originally its own standalone `DESIGN_module_location.md`
before being folded into `DEVELOPMENT.md`; restored here as its own design doc under the
new `specs/design/` convention.

### Problem

Every `Module` already knows its observatory location (`Object._location`/`_observer`/`_timezone`,
set from constructor config in `pyobs/object.py:248-327` and exposed via the `observer`/`location`/
`timezone` properties, `pyobs/object.py:210-225`). Right now this is purely local: other modules or
clients (e.g. the web client, or the FITS-header pipeline) have no way to query a remote module's
site location over comm — each module config just repeats the location block if it needs one.

### Decision: one-shot capabilities, not pubsub state

Location is static for a module's lifetime (set once at construction, not expected to change at
runtime), so publishing it uses the same **one-shot capabilities** mechanism already used for
`ModuleCapabilities` (version/label) — not the pubsub `state` mechanism used for values that change
(`IWeather`, `IMotion`, etc.). This avoids adding subscription overhead to every module (all modules
implement `IModule`) for what is effectively immutable config, and sidesteps the class of bug hit
before where a widely-implemented interface picking up unwanted `state` caused phantom XMPP
subscriptions (see `Interface.has_own_state()` in `pyobs/interfaces/interface.py`).

`Interface.capabilities` is a single `ClassVar[type | None]` slot per interface
(`pyobs/interfaces/interface.py:10`) — there's no mechanism for a second, independent capabilities
dataclass on `IModule`. So location is added as a **nested field inside** `ModuleCapabilities`, not
as a sibling dataclass.

### Caveat: per-module, not a site-wide source of truth

pyobs has no shared "site" concept — each module independently configures its own `location` in
YAML (`pyobs/object.py:248-327`), so two modules belonging to the same observatory could disagree
(typo, copy-paste drift, stale config). Publishing per-module location doesn't fix that, it just
makes it observable for the first time. The published value should be treated as *"this module's
belief about its own location,"* not a canonical site fact. A lightweight warning (see below) makes
disagreement surface in logs rather than silently producing wrong astrometry downstream. Fixing
drift at the config level is handled separately by the existing `{include}`/YAML-anchor mechanism in
`pyobs/utils/config.py` (already used in production to share a `location:` block across module
configs) — this design's warning is a backstop for the case someone forgets to use it, or two
systems get bridged unexpectedly, not a replacement for it.

### Implementation

#### 1. `pyobs/interfaces/IModule.py`

`ModuleLocation` dataclass, nested in `ModuleCapabilities`:

```python
@dataclass
class ModuleLocation:
    longitude: float = 0.0
    latitude: float = 0.0
    elevation: float = 0.0
    timezone: str = "utc"


@dataclass
class ModuleCapabilities:
    label: str = ""
    version: str = ""
    location: ModuleLocation | None = None
```

`location` stays `None` for modules that don't configure one (`Object._location is None`).
`ModuleLocation` exported in `__all__`.

#### 2. `pyobs/modules/module.py` — `Module.open()`

Extends the existing capabilities publish with `location=ModuleLocation(...)` built from
`self._location`/`self._timezone`, or `None` if no location is configured.

#### 3. Comm layer

No changes needed to `pyobs/comm/comm.py` or the XMPP backend (`set_capabilities`/`get_capabilities`
already generic over `(interface, dataclass)` pairs, `pyobs/comm/xmpp/xmppcomm.py`) — this is exactly
why the capabilities mechanism was chosen.

#### 4. Warning on location mismatch

Capabilities are pull-only (no subscription, unlike `state`), so there's no "capabilities changed"
event to hook. But `_on_module_opened` (`pyobs/modules/module.py`) already fires for every peer that
connects and already fetches that peer's `IModule` capabilities via proxy to compare pyobs versions —
so this is the natural, automatic, system-wide place to also compare location. No new subscription,
no opt-in helper that call sites might forget to use: if both sides have a location configured, the
geocentric distance between them is computed via `EarthLocation`, and a `log.warning` fires if it
exceeds 100m.

Every module already discovers every other module it connects to via `ModuleOpenedEvent`, so this
gives full, automatic, system-wide drift detection for free — no extra call sites, no discipline
required.

#### Status

✅ Implemented and merged to `develop` (`pyobs/interfaces/IModule.py`, `pyobs/modules/module.py`,
tests in `tests/comm/test_presence.py`).

