# Check `Interface.state`/`capabilities` by own declaration, not inherited presence

status: accepted
date: 2026-07-02

## Context and Problem Statement

`Interface.state` is a plain class attribute (`ClassVar[type | None] = None`), set by
whichever interface actually owns a state schema (e.g. `IExposure.state = ExposureState`).
Composite interfaces like `ICamera(IData, IExposure)` inherit it via normal Python MRO —
`ICamera.state` resolves to `ExposureState` even though `ICamera` itself never declares a
state schema and no module ever publishes state under the composite interface's own name.

`Comm._get_client` and `XmppComm`'s connect-time disco#info feature registration both used
`interface.state is not None` to decide "does this interface have state, so subscribe/advertise
it" — true for any composite interface that happens to pull in a stateful component, not just
for interfaces that genuinely own one. This produced permanent, silent no-op subscriptions:
`xmppcomm.py` logged `"Could not subscribe to state node pyobs:state:camera:ICamera:1 after 30
attempts"` — a symptom that reads like a network/timing issue but is actually structural, since
the node is never created because nothing ever publishes under that composite name. Affected:
`IAcquisition`, `IAutoGuiding`, `IAutonomous`, `ICamera`, `IDome`, `IRoof`, `ISpectrograph`,
`IStartStop`, `ITelescope` — all inherit `state` from `IRunning`, `IMotion`, or `IExposure`.

## Considered Options

* Leave `interface.state is not None` as the check, and stop composite interfaces from
  inheriting stateful bases (i.e. redesign the interface hierarchy so `ICamera` doesn't
  transitively pull in `IExposure`'s state)
* Add a second, explicit "does this interface directly own a state schema" check, used
  everywhere `interface.state is not None` currently gates subscription/advertisement
  decisions

## Decision Outcome

Chosen option: add `Interface.has_own_state()`, checking `"state" in cls.__dict__` (directly
defined on that exact class, not inherited via MRO) rather than `cls.state is not None`
(true for any class that inherits a non-`None` value from any base). Both call sites
(`Comm._get_client`'s auto-subscribe loop and `XmppComm`'s disco#info feature registration)
were swapped from `interface.state is not None` to `interface.has_own_state()`.

Redesigning the interface hierarchy (option 1) was rejected: `ICamera(IData, IExposure)` and
similar composites are deliberate — a camera genuinely *is* an `IExposure` for typing and
discovery purposes, it just shouldn't re-advertise `IExposure`'s state under its own,
never-published name. The inheritance itself isn't the bug; the presence check was too coarse
to distinguish "inherits a schema" from "owns a schema."

### Consequences

* Good, because the fix is two call sites, not an interface hierarchy redesign
* Good, because it generalizes: any future composite interface pulling in a stateful base is
  automatically correct, no per-interface opt-out needed
* Neutral, because `Interface.capabilities` has the identical shape (`ClassVar[type | None]`)
  and could in principle suffer the same bug — no interface currently inherits `capabilities`
  from a component the way `state` was inherited, so no `has_own_capabilities()` was added
  preemptively. If a capabilities interface is ever composed the same way, apply the identical
  fix rather than assuming it already works.
