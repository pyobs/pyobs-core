# Publish observer's location as part of `IModule` capabilities

## Problem

Every `Module` already knows its observatory location (`Object._location`/`_observer`/`_timezone`,
set from constructor config in `pyobs/object.py:248-327` and exposed via the `observer`/`location`/
`timezone` properties, `pyobs/object.py:210-225`). Right now this is purely local: other modules or
clients (e.g. the web client, or the FITS-header pipeline) have no way to query a remote module's
site location over comm — each module config just repeats the location block if it needs one.

## Decision: one-shot capabilities, not pubsub state

Location is static for a module's lifetime (set once at construction, not expected to change at
runtime), so publishing it uses the same **one-shot capabilities** mechanism already used for
`ModuleCapabilities` (version/label) — not the pubsub `state` mechanism used for values that change
(`IWeather`, `IMotion`, etc.). This avoids adding subscription overhead to every module (all modules
implement `IModule`) for what is effectively immutable config, and sidesteps the class of bug we hit
before where a widely-implemented interface picking up unwanted `state` caused phantom XMPP
subscriptions (see `Interface.has_own_state()` in `pyobs/interfaces/interface.py`).

`Interface.capabilities` is a single `ClassVar[type | None]` slot per interface
(`pyobs/interfaces/interface.py:10`) — there's no mechanism for a second, independent capabilities
dataclass on `IModule`. So location is added as a **nested field inside** `ModuleCapabilities`, not
as a sibling dataclass.

## Caveat: per-module, not a site-wide source of truth

pyobs has no shared "site" concept — each module independently configures its own `location` in
YAML (`pyobs/object.py:248-327`), so two modules belonging to the same observatory could disagree
(typo, copy-paste drift, stale config). Publishing per-module location doesn't fix that, it just
makes it observable for the first time. The published value should be treated as *"this module's
belief about its own location,"* not a canonical site fact. A lightweight warning (see below) makes
disagreement surface in logs rather than silently producing wrong astrometry downstream. Fixing
drift at the config level (shared site config, YAML anchors, etc.) is explicitly out of scope here.

## Implementation

### 1. `pyobs/interfaces/IModule.py`

Add a `ModuleLocation` dataclass and nest it in `ModuleCapabilities`:

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

`location` stays `None` for modules that don't configure one (`Object._location is None`). Export
`ModuleLocation` in `__all__`.

### 2. `pyobs/modules/module.py` — `Module.open()`

Extend the existing capabilities publish:

```python
await self._comm.set_capabilities(
    IModule,
    ModuleCapabilities(
        version=await self.get_version(),
        label=await self.get_label(),
        location=ModuleLocation(
            longitude=self._location.lon.degree,
            latitude=self._location.lat.degree,
            elevation=self._location.height.value,
            timezone=str(self._timezone),
        ) if self._location is not None else None,
    ),
)
```

### 3. Comm layer

No changes needed to `pyobs/comm/comm.py` or the XMPP backend (`set_capabilities`/`get_capabilities`
already generic over `(interface, dataclass)` pairs, `pyobs/comm/xmpp/xmppcomm.py`) — this is exactly
why the capabilities mechanism was chosen.

### 4. Warning on location mismatch

Capabilities are pull-only (no subscription, unlike `state`), so there's no "capabilities changed"
event to hook. But `_on_module_opened` (`pyobs/modules/module.py:208-239`) already fires for every
peer that connects and already fetches that peer's `IModule` capabilities via proxy to compare pyobs
versions — so this is the natural, automatic, system-wide place to also compare location. No new
subscription, no opt-in helper that call sites might forget to use:

```python
async def _on_module_opened(self, event: Event, sender: str) -> bool:
    """React to other modules connecting."""
    if sender == self.comm.name or not isinstance(event, ModuleOpenedEvent):
        return False

    # get proxy and version
    try:
        async with self.proxy(sender, IModule) as proxy:
            caps = proxy.get_capabilities(IModule)
            module_version = caps.version if caps is not None else ""
            remote_location = caps.location if caps is not None else None
    except exc.RemoteError:
        return True

    # ... existing version comparison ...

    # compare location, if both sides have one configured
    if remote_location is not None and self._location is not None:
        remote = EarthLocation.from_geodetic(
            remote_location.longitude, remote_location.latitude, remote_location.elevation
        )
        distance = (remote.itrs.cartesian - self._location.itrs.cartesian).norm()
        if distance.to_value("m") > 100:  # tolerance, tune as needed
            log.warning(
                "Module %s reports a location %.0fm from ours (lon=%.4f, lat=%.4f, elevation=%.1fm).",
                sender, distance.to_value("m"),
                remote_location.longitude, remote_location.latitude, remote_location.elevation,
            )

    # okay
    ...
```

Every module already discovers every other module it connects to via `ModuleOpenedEvent`, so this
gives full, automatic, system-wide drift detection for free — no extra call sites, no discipline
required. (In production, the `{include}` config mechanism should make actual drift rare; this is a
backstop for the case someone forgets to use it, or two systems are bridged unexpectedly.)

### 5. Consumers

Anything currently reading `self._observer`/`self._location` directly on a *local* module (e.g.
`pyobs/mixins/fitsheader.py:173-183`, `basetelescope.py:270-275`) does not need to change — those
keep using their own local config.

## Files to change

- `pyobs/interfaces/IModule.py` — add `ModuleLocation` dataclass, nest it in `ModuleCapabilities`,
  update `__all__`.
- `pyobs/modules/module.py` — publish `ModuleLocation` in `open()`; add `get_remote_location()`
  helper with the mismatch warning.
- Unit tests near existing capabilities tests (search `tests/` for `ModuleCapabilities` usage to
  find the right test file and follow its pattern).

## Verification

- Run the existing test suite section covering `IModule`/capabilities (locate via
  `grep -r ModuleCapabilities tests/`) and add a test asserting `ModuleLocation` is published with
  correct lon/lat/elevation/timezone after `Module.open()`, and `None` when no location is
  configured.
- Add a test for `get_remote_location()`: two modules with matching locations produce no warning;
  two modules with differing locations produce a `log.warning` call (assert via `caplog`).
- Manually instantiate a `Module` subclass with a `location` config, open it against a comm, and
  call `comm.get_capabilities(name, IModule)` to confirm `ModuleLocation` round-trips correctly.
- Run `ruff` and `pyrefly` (this repo's configured lint/type-check tools, see `pyproject.toml`)
  since capabilities dataclasses are typed.
