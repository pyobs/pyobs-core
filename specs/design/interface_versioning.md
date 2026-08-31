# Additive interface versioning (IDome, IDomeV2, ...)

Status: proposed (issue #819). Sanity-checked against `develop` (2026-08-28); not yet
implemented, no plan yet. The proposal itself explicitly defers a design doc/plan until the
checks below are accepted — this document is the result of that sanity check, so the
"Gaps" section is the proposal's required additions, not settled decisions.

Repos: pyobs-core (interfaces, discovery, XMPP wire), pyobs-gui (isinstance-based widget
probing), driver plugins (pyobs-*, hardware plugins implement the interfaces).

## Problem

Interfaces (`ICamera`, `IDome`, `ITelescope`, ...) are single-version today. Adding a method
to an existing interface is a breaking change for every module across pyobs-core and sibling
repos that implements it, since ABC subclasses must implement every abstract method. In
practice this means we either avoid extending interfaces or invent awkwardly-named new ones.

## Proposal

Let an interface gain versions within a major release of pyobs-core, each version a strict
superset of the previous one.

- `IDome` (unsuffixed) always means V1, permanently, for the lifetime of the current major
  version. It is never reassigned to a later version.
- Adding a capability means a new class, e.g. `IDomeV2(IDome)`, that only *adds* abstract
  methods — it must never override or remove anything V1 already defines.
- Composite interfaces extend the same way, one level up: to expose a new version of a
  component, the composite's new version inherits **both** its own previous version and the
  upgraded component, e.g. `IDomeV2(IDome, IRoofV2)`. Inheriting `IDome` (not just `IRoof`,
  `IPointingAltAz`) is required — otherwise `isinstance(x, IDome)` stops holding for
  `IDomeV2` implementers, which breaks the "V1 is always safe to assume" guarantee this whole
  scheme exists to provide.
- A module implementing `IDomeV2` automatically satisfies `isinstance(x, IDome)` too, so
  consumers (pyobs-gui, etc.) can always treat V1 as a safe baseline and probe for `VN`
  add-ons via `isinstance`.
- Real breaking changes (removing or changing a method's semantics) are only allowed when
  we're willing to reset the version chain, i.e. at a pyobs-core major-version bump — at
  which point the new unsuffixed baseline may either inherit the old chain's latest version
  for continuity or be a clean break (not mandated either way).

### Rules to enforce

- CI/lint check: `VN+1.__dict__` must not overlap with anything already defined in `VN` (or
  any ancestor version) — additive only, checked mechanically, not just by convention.
- The unsuffixed name must never become an alias for "latest". `class Foo(IDome)` is
  resolved against whatever `IDome` means at import time; if that binding could move to
  `IDomeV2` in a later pyobs-core release, every existing driver that just upgrades
  pyobs-core (without touching its own code) would suddenly need to implement V2's methods
  too, and fail to instantiate.

## Relationship to the existing wire versioning

This proposal deliberately *replaces the meaning* of the version number introduced in
[`pyobs_2_0_wire_protocol.md`](pyobs_2_0_wire_protocol.md): there, `Interface.version`
(`pyobs/interfaces/interface.py:10`) is one number per interface that a developer bumps on a
breaking change, with everything downstream (disco#info features, state namespaces, PubSub
node paths) derived from it — the same-name "reassign to latest" model this proposal rejects.
Under additive versioning the number describes the contract level of the *class itself*
(`IDome` is v1 forever, `IDomeV2` is v2), and the class name carries the chain position. The
wire format itself needs no change — it already encodes `{name}:{version}`.

## Sanity check against current code (2026-08-28)

All checks run against the real interfaces (`pyobs/interfaces/*`) with versioned subclasses
defined the way the proposal prescribes.

### MRO/diamond — verified

`IDomeV2(IDome, IRoofV2, IPointingAltAzV2)` (real `IDome(IRoof, IPointingAltAz)`,
`IRoof(IMotion)`, `IMotion(IReady)`) linearizes cleanly under C3:

```
IDomeV2 → IDome → IRoofV2 → IRoof → IMotion → IReady → IPointingAltAzV2
        → IPointingAltAz → Interface → object
```

`isinstance(dome, IDome)` holds for a concrete `IDomeV2` implementer, as does
`isinstance(dome, IRoofV2)`, `isinstance(dome, IPointingAltAz)`, etc. The issue's
MRO/diamond open question resolves favorably for the gnarly composite case.

### Registration — verified

`Interface.__init_subclass__` (`pyobs/interfaces/interface.py:16-43`) registers by
`cls.__name__` in a module-level `_REGISTRY`, raising a `TypeError` on name clashes, and only
for classes whose bases are all "pure" (Interface itself or already-registered). Versioned
chains (`IRoofV2(IRoof)`) and composites (`IDomeV2(IDome, IRoofV2)`) both register cleanly;
`registered_interfaces()` (`interface.py:74`) and `get_registered_interface()` (`interface.py:69`)
need no changes. The name-clash `TypeError` is also a mechanical backstop against two classes
claiming the same versioned name.

### Discovery — verified

`Module._get_interfaces_and_methods()` (`pyobs/modules/module.py:543`) iterates
`registered_interfaces().values()` and does `isinstance(self, interface)`, so a V2 dome
advertises `IDome`, `IDomeV2`, `IRoof`, `IRoofV2`, `IPointingAltAz`, `IPointingAltAzV2`,
`IMotion`, `IReady` for free — no new plumbing, exactly as the proposal claims. The ACL
interface-name sugar in `_expand_acl_entries` (`module.py:525`) keys on
`interface.__name__`, so `"IDomeV2"` also works as an ACL `allow` entry.

### Wire round-trip — verified, with one required addition (see Gap 1)

The XMPP side already forwards the same list, versioned:

- Publisher: `XmppComm._connect` (`pyobs/comm/xmpp/xmppcomm.py:353-356`) adds a disco#info
  feature `urn:pyobs:interface:{name}:{version}` per interface in `Module.interfaces` (and
  `urn:pyobs:state:{name}:{version}` for interfaces with own state).
- Receiver: `_get_interfaces` (`xmppcomm.py:494-540`) resolves each feature back to the local
  registered class and **hard-matches** `str(local_cls.version) == version`; names that don't
  match are silently dropped, not errored.

Consequences, verified: a V1-only consumer (old pyobs-core, no `IDomeV2` registered) seeing a
V2 dome's features keeps only `IDome:1` — `IDomeV2:2` is invisible. A V2-aware consumer sees
both. `_interface_names_to_classes` (`pyobs/comm/comm.py:335`) maps both back to classes, and
`has_interface`/`_supports_interface` (`xmppcomm.py:617`) answer per-name. State semantics are
unaffected: `has_own_state()` (`interface.py:59-66`) correctly reports False for `IDomeV2`
(no own `state`), so V2 domes keep publishing state under the V1 defining interface
(`IPointingAltAz:1`), and `Comm._get_client` (`comm.py:147-150`) subscribes using the
un-deduped interface list.

## Gaps the proposal must close before a plan

### 1. `version` must be set explicitly per versioned class

`Interface.version` defaults to `1` (`interface.py:10`) and is what the wire encodes
(`xmppcomm.py:354`) and hard-matches (`xmppcomm.py:538-540`). A proposal that doesn't say
"`IDomeV2` sets `version = 2`" leaves the wire advertising `IDomeV2:1` — version 2 by name,
version 1 on the wire. The rule should be: every versioned class sets `version` to its own
chain level. Note the pre-existing quirk that `IModule` opts out with `version: str = ""`
(`pyobs/interfaces/IModule.py:21`), and that `_diagnose_missing_interface`
(`xmppcomm.py:584-615`) already gives users a readable same-name mismatch diagnostic
("Remote implements it at vN, this client expects vM") that the additive scheme can lean on.

### 2. `Proxy` dedup hides V1 from `proxy.interfaces`

`Proxy.__init__` (`pyobs/comm/proxy.py:44-51`) removes any interface that is a superclass of
another listed interface, so a V2 dome's proxy keeps only the most-derived interface
(`IDomeV2`) — `IDome in proxy.interfaces` is False even though the dome implements V1. This
does not break `isinstance(proxy, IDome)` (the proxy's dynamic class inherits the whole
chain, `proxy.py:56-58`) or `comm.proxy(name, IDome)` (`comm.py:200` checks isinstance), and
it is pre-existing behavior for V1 composites (a plain `IDome` dome's proxy already drops
`IRoof`/`IPointingAltAz`/`IMotion`). But the "V1 is always a safe baseline" guarantee should
document that the correct probes are `isinstance` / `has_interface`, not `proxy.interfaces`.

### 3. The additive-only CI rule needs a refined definition

A naive `VN+1.__dict__ ∩ ancestors.__dict__` check flags bookkeeping every class carries:
`__module__`, `__doc__`, `__abstractmethods__`, `_abc_impl`, `__static_attributes__`,
`__firstlineno__`, plus `version` itself (verified: that is exactly the overlap set for a
correctly-written `IDomeV2`). The check must whitelist those (or compare only method names,
optionally with signatures, excluding dunders and ABC internals) and treat `version` as
expected-to-differ metadata.

## Cross-repo impact

- **pyobs-gui** probes via `async with self.comm.proxy(module, IMotion)`-style calls
  (e.g. `pyobs-gui/pyobs_gui/roofwidget.py:59`), i.e. isinstance checks on the proxy
  (`comm.py:200`). Old GUIs (old pyobs-core) keep working against V1 domes and cannot see V2
  interfaces at all (not registered → filtered on the wire). New GUIs probing `IDome` succeed
  against both V1 and V2 domes; probing `IDomeV2` succeeds only against V2 domes — the opt-in
  the proposal wants.
- **Driver plugins** opt in by changing `class MyDome(Module, IDome)` to
  `class MyDome(Module, IDomeV2)`; a plugin that does nothing keeps implementing V1 forever
  and remains fully compatible. This is the intended friction (the opt-in signal), and the
  proposal's ergonomics note (a lint hint that a newer version exists) would soften it.
- Worth a follow-up scan of which sibling repos use `proxy.interfaces` (rather than
  isinstance/has_interface) before landing, given Gap 2.

## What a plan would need to cover

1. First versioned interface + composite pair (issue names `IDome`/`IRoof`) as the pilot,
   including the concrete `IDomeV2` definition and the `version` attribute rule (Gap 1).
2. The mechanical additive-only lint check (Gap 3), as a CI step.
3. A decision on documenting/possibly adjusting the `Proxy` dedup guarantee (Gap 2).
4. The cross-repo scan (pyobs-gui + driver plugins) and a decision on whether any existing
   interface genuinely needs a V2 in the current major, or whether the scheme lands with the
   mechanism + lint check and no versioned interface yet.
