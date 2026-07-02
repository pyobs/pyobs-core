# Towards pyobs 2.0 — v0.47 (2026-07-01, 20:00)

## Status

Design exploration turned implementation log. Most of what this document proposed is now built and merged to `develop` (version, state, capabilities, presence, disco#info schema publication, RPC payload encoding 2.0, the `async with`-only `Proxy` redesign, the mixed-version-fleet diagnostic) — checked directly against the code while revising this pass, not just against the document's own earlier self-reported notes, several of which had gone stale. ✅ marks a point confirmed implemented; remaining unmarked items are genuinely still open. Two corrections surfaced during this pass, noted where relevant: there is no D-Bus `Comm` backend in `pyobs-core` (only `xmpp`, `local`, `dummy`), and `ILatLon`/`LatLonCapabilities` no longer exist in `pyobs.interfaces` — both are left as historical context where the reasoning still applies, corrected where it was stated as current fact.

## Table of Contents

- [Motivation](#motivation)
- [Current Architecture Assessment](#current-architecture-assessment)
  - [What's already right](#whats-already-right)
  - [Where XMPP is underused](#where-xmpp-is-underused)
- [Proposed Direction](#proposed-direction)
  - [1. Capabilities / Discovery](#1-capabilities--discovery)
  - [2. Commands (RPC) — unchanged](#2-commands-rpc--unchanged)
  - [3. State — the one new concept](#3-state--the-one-new-concept)
    - [Handling state that isn't fully fixed by the interface](#handling-state-that-isnt-fully-fixed-by-the-interface)
  - [4. Events — unchanged at the API level](#4-events--unchanged-at-the-api-level)
- [Wire Protocol](#wire-protocol)
  - [Payload Encoding](#payload-encoding)
  - [RPC Payload Encoding 2.0](#rpc-payload-encoding-20)
  - [Type Vocabulary](#type-vocabulary)
    - [What the vocabulary above is actually built from](#what-the-vocabulary-above-is-actually-built-from)
  - [Enums in RPC and State](#enums-in-rpc-and-state)
  - [Units](#units)
  - [Versioning](#versioning)
  - [Thought experiment: a client in a fixed-type language (C/Java)](#thought-experiment-a-client-in-a-fixed-type-language-cjava)
- [Impact Analysis](#impact-analysis)
  - [By Comm backend](#by-comm-backend)
  - [The one genuine cross-backend change](#the-one-genuine-cross-backend-change)
  - [Important constraint](#important-constraint)
- [Implementation Sketch: State on `Comm` and `Proxy`](#implementation-sketch-state-on-comm-and-proxy)
  - [`Comm`: three new abstract methods](#comm-three-new-abstract-methods)
  - [`Proxy`: state hidden behind `update_state` and a `state` method](#proxy-state-hidden-behind-update_state-and-a-state-method)
  - [Lifecycle: piggyback on existing proxy eviction, no new `Proxy` API](#lifecycle-piggyback-on-existing-proxy-eviction-no-new-proxy-api)
  - [Reconnect with a different interface set](#reconnect-with-a-different-interface-set)
  - [Final decision: `async with` only — `await self.proxy()` is removed](#final-decision-async-with-only--await-selfproxy-is-removed)
  - [Migration patterns from real call sites](#migration-patterns-from-real-call-sites)
  - [XMPP backend: concrete implementation](#xmpp-backend-concrete-implementation)
- [Summary](#summary)
- [Open Questions / Next Steps](#open-questions--next-steps)
- [Work Plan](#work-plan)
  - [Phase 0 — Foundations](#phase-0--foundations)
  - [Phase 1 — Walking skeleton: prove State end-to-end on one interface](#phase-1--walking-skeleton-prove-state-end-to-end-on-one-interface)
  - [Phase 1.5 — RPC payload encoding 2.0](#phase-15--rpc-payload-encoding-20)
  - [Phase 2 — Audit and design pass (no implementation yet)](#phase-2--audit-and-design-pass-no-implementation-yet)
  - [Phase 2.5 — Discovery and Presence](#phase-25--discovery-and-presence)
  - [Phase 3 — Bulk rollout](#phase-3--bulk-rollout)
  - [Phase 4 — Other backends and Presence](#phase-4--other-backends-and-presence)
  - [Phase 5 — `pyobs-gui`](#phase-5--pyobs-gui)
  - [Phase 6 — External official `pyobs-*` hardware modules](#phase-6--external-official-pyobs--hardware-modules)
  - [Phase 7 — `pyobs-web-client` catch-up](#phase-7--pyobs-web-client-catch-up)
- [Appendix: `get_*` to State Survey](#appendix-get_-to-state-survey)
- [Appendix: State and Capability dataclass catalogue](#appendix-state-and-capability-dataclass-catalogue)

## Motivation

pyobs's communication layer is built on three pillars:

1. **Remote procedure calls (RPC)**
2. **Interface discovery**
3. **Events**

These map onto XMPP reasonably well today, and the choice of XMPP as the transport for a distributed observatory control system (10–100 agents, needing addressing, authentication, encryption, and no custom broker) remains sound. However, a closer look shows pyobs is **underusing** XMPP rather than misusing it: several XMPP-native mechanisms (Presence, PubSub, Service Discovery extensions) could replace bespoke patterns, and the ongoing development of a non-Python web client (`pyobs-web-client`) is exactly the kind of pressure that typically pushes a project from "shared Python library" to "explicit wire protocol."

This document summarizes that assessment and lays out a concrete design direction for pyobs 2.0.

## Current Architecture Assessment

| Part | Rating | Comments |
|---|---|---|
| XMPP choice | ★★★★★ | Excellent fit for a distributed observatory control system |
| Service discovery of interfaces | ★★★★★ | One of the best design choices already in place |
| Service discovery of methods | ★★★☆☆ | Useful, but only as optional introspection metadata |
| Event system | ★★★★☆ | Good, but could leverage XMPP PubSub (XEP-0060) |
| RPC | ★★★★☆ | Good abstraction (`proxy()` pattern); should not be used for continuous state polling |
| Use of XMPP features | ★★★☆☆ | Presence and PubSub are largely unexploited |

### What's already right

- **XMPP as transport**: JIDs as globally unique addresses, a mature server ecosystem, authentication/encryption, async messaging, and a request/response model via IQ stanzas all match pyobs's needs as a distributed system of independent, comings-and-goings agents.
- **Interface-level discovery (XEP-0030)**: distributing *interfaces* (`ICamera`, `ICooling`, ...) rather than individual methods is the right abstraction level. Discovery answers "who can take an image?" without exposing implementation details like `_flush_buffer` or `reset_usb`.
- **The `proxy()` abstraction**: `camera = await self.proxy("camera", ICamera)` cleanly hides the communication layer behind a typed interface — this pattern should be preserved.
- **Event-driven pub/sub style**: events are naturally asynchronous, one-to-many, and loosely coupled, and are already a clear improvement over callback-based designs.

### Where XMPP is underused

**Presence.** Modules have natural states — online/offline, idle, busy, error, maintenance — that map almost directly onto XMPP presence. Today this kind of information risks being reinvented as custom events. A cleaner split:

| Information | XMPP mechanism |
|---|---|
| Module exists | Presence |
| Module available | Presence |
| Busy / idle | Presence status |
| Weather changed | Event |
| Exposure finished | Event |
| Telescope moved | Event |

**PubSub (XEP-0060).** Events are currently sent as a custom broadcast (`send_event(Event)`). XMPP's standard pub/sub extension would let the server handle subscriptions, support late joiners receiving persisted events, allow fine-grained permissions, and reduce traffic. For an observatory, where many events (e.g. small temperature fluctuations) are genuinely transient and uninteresting to a freshly-restarted GUI, a lightweight custom broadcast can still be the right call for low-value chatter — but high-level events and **state streams** are good PubSub candidates.

**RPC overuse for status.** RPC is excellent for commands (`move telescope`, `open dome`, `start exposure`) but is easy to overuse for status queries (`get_temperature()`, `get_status()`). Repeated polling creates long dependency chains (Mastermind → Telescope → Mount → Encoder) where the whole system depends on a chain of live connections. A **state/event model** — where modules publish current values and clients subscribe — removes this coupling and reduces traffic.

## Proposed Direction

Keep the existing architecture (RPC + interfaces + events) but extend it with a fourth, currently-missing concept: **state**. Each module exposes four kinds of information:

| Kind | Question it answers | Typical transport |
|---|---|---|
| **Capabilities** (interfaces, commands, state schema, events) | What can you do? | XMPP Service Discovery (XEP-0030) |
| **Commands** | Do something! | XMPP IQ (RPC) |
| **State** | What is true right now? | XMPP PubSub |
| **Events** | What happened? | XMPP PubSub or messages |

This gives a clean separation of concerns:

```
Presence
  camera@obs is online

Service discovery
  I support:
      ICamera v2
      ICooling v1

  ICamera:
      commands
      state schema
      events

RPC
  expose(10)

PubSub state
  temperature = -20
  status = exposing

Events
  ExposureFinished(file)
```

### 1. Capabilities / Discovery

✅ **Implemented.**

A module does not continuously publish its interfaces and commands — this is metadata that changes rarely, so XEP-0030 discovery is the right mechanism. On connect, a module advertises:

```
camera@obs

interfaces:
  ICamera
  ICooling

ICamera:
  commands:
    expose(exposure_time)
    abort()
  events:
    ExposureFinished
    ExposureFailed

ICooling:
  commands:
    set_setpoint(float)
    set_enabled(bool)
  state:
    ICooling.State
```

Since pyobs already has Python interface definitions, advertising just the interface *name* (`ICooling`) is sufficient for pyobs-native clients, which already know what that interface means. **Full method/state/event introspection only needs to be published for the benefit of non-Python clients** (web GUIs, or other language bindings) — this is the key argument for extending discovery output, driven directly by the needs of `pyobs-web-client`.

Discovery should remain reserved for relatively static information: interfaces, commands and signatures, state schema, event definitions, versions, documentation URLs. It is *not* intended for runtime values (current temperature, current RA/Dec, busy state, image progress) — those belong in PubSub.

**Publishing state in discovery follows the same disco#info extension already used for commands and events — one `<state>` child element per interface, inside that interface's own `<pyobs:interface>` block, schema only, never live values.** A module implementing several small interfaces ends up with *multiple* self-contained blocks in one disco#info reply, each carrying its own `<state>` only if that interface declares one — there's no single block that owns "the state" for the whole module.

Two additions, neither decided elsewhere in this document:

- **A `<feature var="urn:pyobs:state:{Name}:{version}"/>` entry**, parallel to the existing `urn:pyobs:interface:...` feature. Without it, checking "does this module publish state for `ICooling`" requires parsing the custom payload; with it, the same cheap XEP-0030 feature-matching `pyobs-web-client` already does for interfaces works for state too.
- **An explicit `node` attribute on `<state>`**, giving the PubSub node path directly instead of every client constructing `state/{Name}/{version}` itself. The path is fully derivable from information the client already has, so this is redundant rather than new — but the schema is machine-generated regardless, so emitting one more derived field costs nothing and removes a place a generated C/Java binding could get the formatting subtly wrong.

XEP-0030 is extensible via custom namespaces, so this introspection can sit directly inside disco#info responses without breaking standard XMPP clients, which simply ignore unrecognized elements. A module implementing `IGain`, `IImageFormat`, and `ICooling` together — not one aggregated state, three independent ones:

```xml
<iq type="result">
  <query xmlns="http://jabber.org/protocol/disco#info">
    <identity category="pyobs" type="module" name="camera"/>

    <feature var="urn:pyobs:interface:IGain:1"/>
    <feature var="urn:pyobs:state:IGain:1"/>
    <feature var="urn:pyobs:interface:IImageFormat:1"/>
    <feature var="urn:pyobs:state:IImageFormat:1"/>
    <feature var="urn:pyobs:interface:ICooling:1"/>
    <feature var="urn:pyobs:state:ICooling:1"/>

    <pyobs:interface xmlns:pyobs="urn:pyobs:interface:IGain:1" name="IGain">
      <command name="set_gain">
        <parameter name="gain" type="float64"/>
      </command>
      <state name="State" node="state/IGain/1">
        <field name="gain" type="float64"/>
        <field name="offset" type="float64"/>
      </state>
    </pyobs:interface>

    <pyobs:interface xmlns:pyobs="urn:pyobs:interface:IImageFormat:1" name="IImageFormat">
      <types>
        <enum name="ImageFormat">
          <value>int8</value>
          <value>int16</value>
          <value>float32</value>
          <value>float64</value>
          <value>rgb24</value>
        </enum>
      </types>
      <command name="set_image_format">
        <parameter name="format" type="enum(ImageFormat)"/>
      </command>
      <state name="State" node="state/IImageFormat/1">
        <field name="format" type="enum(ImageFormat)"/>
      </state>
    </pyobs:interface>

    <pyobs:interface xmlns:pyobs="urn:pyobs:interface:ICooling:1" name="ICooling">
      <command name="set_cooling">
        <parameter name="enabled" type="bool"/>
        <parameter name="setpoint" type="float64" unit="celsius"/>
      </command>
      <state name="State" node="state/ICooling/1">
        <field name="enabled" type="bool"/>
        <field name="setpoint" type="float64" unit="celsius"/>
        <field name="power" type="float64" unit="percent"/>
        <field name="temperature" type="float64" unit="celsius"/>
      </state>
    </pyobs:interface>

  </query>
</iq>
```

Each block is independently meaningful — a client that only cares about `ICooling` can ignore the other two entirely, and a module that implements only `IGain` (outside `pyobs-core`, on its own) would publish exactly that one block and nothing else. A client's actual consumption flow: one disco#info query gets all three schemas at once (no per-interface round trip); for each `<state>` present, read `node` (or derive `state/{Name}/{version}` if a client chooses not to rely on the attribute) and subscribe via XEP-0060, which — per the "deliver the last item immediately" semantics already designed — hands back the current value on subscribe without a separate fetch. `set_cooling`'s `setpoint` parameter carries the same `unit="celsius"` the `CoolingState.setpoint` field does, generated from the same `Annotated[float, Unit.CELSIUS]` source in both places — one annotation, not two things to keep in sync by hand.

**A third disco#info element for values that fit neither `<command>` (asked each time) nor `<state>` (pushed over a separate PubSub subscription): `<capability>`, for values fixed for the module's lifetime, published inline in the same reply that already announces the interface.** No new `Comm` abstraction needed — capabilities ride entirely on the disco#info mechanism every backend already implements — and no new `<feature var>` needed either, unlike state: state needs its own flag because it gates a *separate* mechanism a client decides whether to subscribe to, while a capability is already sitting in the reply a client has, no separate yes/no gate to check first.

`IWindow` has one of each, which makes it a good worked example: `get_full_frame` is fixed for the module's lifetime (the CCD doesn't resize itself) — discovery. `get_window` changes whenever `set_window` is called — state.

```xml
<pyobs:interface xmlns:pyobs="urn:pyobs:interface:IWindow:1" name="IWindow">

  <!-- fixed for the module's lifetime -- published directly, no RPC round trip -->
  <capability name="full_frame" type="struct(Window)">
    <field name="left" type="int32">0</field>
    <field name="top" type="int32">0</field>
    <field name="width" type="int32">2048</field>
    <field name="height" type="int32">2048</field>
  </capability>

  <command name="set_window">
    <parameter name="left" type="int32"/>
    <parameter name="top" type="int32"/>
    <parameter name="width" type="int32"/>
    <parameter name="height" type="int32"/>
  </command>

  <!-- changes whenever set_window is called -- published live -->
  <state name="State" node="state/IWindow/1">
    <field name="left" type="int32"/>
    <field name="top" type="int32"/>
    <field name="width" type="int32"/>
    <field name="height" type="int32"/>
  </state>

</pyobs:interface>
```

A scalar capability is the same shape with no nested `<field>`s needed — `IModule.get_version` would just be `<capability name="version" type="string">2.0.1</capability>`. Same mechanism for `IModule.get_label` and `IMultiFiber.get_fiber_count` from the [get_* to State Survey](#appendix-get_-to-state-survey)'s Discovery bucket — none of them need their own worked example, the pattern is identical. (`ILatLon`/`get_latlon`, cited here in the original draft, no longer exist in `pyobs.interfaces` — removed independently of this document.)

✅ **Resolved, further than proposed.** `get_full_frame` isn't just redundant once `full_frame` is a capability — on `develop` it's gone entirely: `IWindow` has no `get_full_frame` abstract method at all anymore, only `state = WindowState` and `capabilities = WindowCapabilities`. Same for `ICooling.get_cooling` — removed, not merely superseded.

This means the script currently used to extract interface information for `pyobs-web-client` could be eliminated: the client could query disco#info directly instead of maintaining a separate extraction step.

### 2. Commands (RPC) — unchanged

Existing RPC stays as-is: `await camera.expose(10)` continues to map onto an XMPP IQ round-trip. No changes are required here beyond what discovery already exposes.

### 3. State — the one new concept

✅ **Implemented.**

This is the significant addition. Today pyobs has no first-class concept of continuously-published, cached, latest-known values. The proposal:

```python
@dataclass
class CoolingState:
    temperature: float
    setpoint: Annotated[float, Unit.CELSIUS]
    power: float
    enabled: bool
    time: Time = field(default_factory=Time.now)

class ICooling(Interface):
    state = CoolingState

    async def set_enabled(self, enabled: bool):
        ...

    async def set_setpoint(self, value: float):
        ...
```

A module updates its state via the communication layer, never touching transport details directly:

```python
self.set_state(
    ICooling,
    CoolingState(temperature=-20, power=65),
)
```

```
Module
   |
   | set_state()
   v
pyobs communication
   |
   +-- cache current state
   +-- publish via XMPP PubSub
   +-- serialize to XML
```

State has no history — it answers only "what is the latest known value?" — distinguishing it clearly from events, which are immutable, timestamped facts about things that happened (`ExposureStarted`, `DomeOpened`, `ErrorOccurred`).

#### Handling state that isn't fully fixed by the interface

✅ **Implemented** — `ITemperatures.state = TemperaturesState`, `readings: list[SensorReading]`, matching this design exactly.

Not all state fits a fixed schema. A telescope's temperature sensors, for example, vary by hardware: different telescopes have sensors at different physical locations with different names. A strict "all state is defined by the interface" approach is too rigid for this. The recommended pattern is **extensible state with typed collections**, where the interface guarantees structure and semantics but not exact field names:

```python
@dataclass
class TemperatureSensor:
    id: str
    value: float
    unit: str = "C"

class ITemperatures(Interface):
    @dataclass
    class State:
        sensors: list[TemperatureSensor]
```

The interface guarantees there is a collection of named temperature sensors with values; it does not guarantee which sensors exist. One telescope might publish `primary_mirror`, `secondary_mirror`, `truss`, `camera_flange`; another might publish `mirror`, `dome_air`. A generic GUI knows how to display a list of sensors by id/value (and could plot them over time) without knowing the specific sensor names in advance.

This mirrors the pattern used by mature distributed control systems (EPICS, OPC UA, ROS): fixed schemas for common concepts, extensible collections for hardware-specific detail. Approaches considered and rejected:

- **Plain `dict[str, float]`** — works, but loses self-description (no units, no metadata).
- **Hardcoded fields** (`temperature1`, `temperature2`, ...) — breaks as soon as hardware changes.
- **RPC-style querying** (`get_temperature("mirror")`) — reintroduces polling and loses the benefits of state distribution.
- **Splitting into a generic + specialized interface** (`ITemperatures` for generic tools, `ITelescopeThermalControl` for a dedicated GUI) — a valid complementary pattern when truly device-specific structure is needed, following the "small interfaces" philosophy already used elsewhere in pyobs.
- **Dynamically-advertised per-device schemas** (the OPC UA pattern — each device exposes its own genuinely different, individually-named/typed fields, discoverable only by querying that specific instance) — **decided against.** Schemas stay per-interface, fixed and known statically from the Python type; only the data varies between devices, never the shape. Avoids discovery having to handle two independent kinds of variability (per-interface and per-device) for a need the extensible-collection pattern already covers.

### 4. Events — unchanged at the API level

Event classes already define a schema today (e.g. `class ExposureFinished(Event): filename: str`). The communication layer can introspect this for discovery (name, fields, types) and publish it alongside interface metadata. Runtime delivery can stay exactly as it is; only the *discovery* of event schemas is new.

**Events and state use different XMPP mechanisms underneath, which is why "unchanged" is correct here rather than just convenient.** `register_event`'s real implementation doesn't do XEP-0060 PubSub subscribe at all — it's XEP-0163 (PEP): `self.client["xep_0163"].add_interest(...)` followed by `update_caps()` and `send_presence()`. Interest is broadcast via your own presence/capabilities hash, not established via a per-subscription IQ handshake the way state's PubSub subscribe will be. That's *why* `register_event` has no corresponding `unregister_event` in the real codebase today, and why it doesn't need one the way state needs `unsubscribe_state`: there's no server-side subscription resource being held open to leak. State's `unsubscribe_state` exists because XEP-0060 PubSub subscriptions are real, accumulating server-side resources if never released — and it has a natural place to hook into release, because `Proxy` (and therefore each state subscription) is already scoped to one specific remote module, already evicted on that module's disconnect. Event registration isn't scoped to any one remote peer in the first place — `register_event(NewImageEvent, handler)` means "from anyone," not "from module X" — so there's no analogous per-peer disconnect trigger that would even make sense as an unsubscribe point for it.

**Naming follows the same pattern as interfaces — `urn:pyobs:event:NewImageEvent:1` — and versioning is independent, each `Event` class carrying its own `version`**, rather than inheriting a version from an owning interface.

Most events aren't owned by a single interface at all. `NewImageEvent`, for example, is fired by eight modules spanning camera, image-processing, and pointing/guiding code — modules that don't all implement the same interfaces, let alone the same interface version. So "inherit the owning interface's version" usually has no single interface to inherit from in the first place, and even where one exists, two `ICamera`-implementing modules at different `version`s firing an unchanged `NewImageEvent` would otherwise advertise the identical event under two different namespace strings for no real reason.

```python
class NewImageEvent(Event):
    version: int = 1
    filename: str
    image_type: ImageType | None = None
```

`urn:pyobs:event:NewImageEvent:{version}` derives from the event class itself — mechanically identical to `Interface.version`, just answering a question ("what changed about this event's schema") that's genuinely independent of any one interface's command/state contract, because the event was never that interface's to version in the first place.

✅ `Event.version: int = 1` exists on `develop`, same as `Interface.version`. 🔵 **Still not done:** the wire side — `add_feature(f"pyobs:event:{ev.__name__}")` in `xmppcomm.py` still publishes the bare pre-2.0 form, not `urn:pyobs:event:{name}:{version}`. Event schema publication in disco#info hasn't started either. This was deliberately left out of scope when the interface-feature versioning landed (see the mixed-version-fleet fix in Open Questions below) and is still open — see Phase 0/Phase 3 in the Work Plan.

## Wire Protocol

### Payload Encoding

✅ **Implemented** — native XML, `pyobs/comm/xmpp/serializer.py`.

A secondary question, raised once state-over-XMPP is on the table: what format should state payloads use, given XMPP itself is XML?

| Option | Summary | Verdict |
|---|---|---|
| **XML payloads** (native namespaces, e.g. `urn:pyobs:state:ICooling:1`) | Mirrors dataclasses directly into XML elements; integrates naturally with XMPP namespaces and PubSub items; can be schema-validated | **Recommended** |
| **JSON inside XML** | Easy to map from Python dataclasses, good tooling, easy for web clients | Common in the wild, but loses XML namespace/schema benefits |
| **XMPP Data Forms (XEP-0004)** | Standardized structure, existing library support | Designed for forms/discovery, not high-frequency telemetry; verbose |
| **Binary encoding (MessagePack/CBOR)** | Compact, fast | Debugging becomes painful; overkill for an observatory-scale network |

**Recommendation: XML**, because pyobs already depends heavily on XMPP-native concepts (JIDs, service discovery, IQ requests, presence). Leaning into XMPP rather than treating it as a generic message tunnel is the more coherent long-term direction, and interfaces already have natural names that map onto namespaces (`ICooling → urn:pyobs:state:ICooling:1`) — versioned and capitalized to match the interface naming scheme settled on above, since a state schema is part of the same contract as the interface's commands, not a separate thing with its own version lineage (events are the one exception to this — see Events above). A breaking change to `CoolingState`'s fields bumps `ICooling` to v2 exactly the same way a breaking change to `set_setpoint`'s signature would.

Critically: **the dataclass should define the schema, and XML should be generated automatically from it.** Hand-maintaining the Python interface, the XMPP schema, and documentation as three separate sources of truth would be a maintenance trap.

### RPC Payload Encoding 2.0

✅ **Implemented** — `pyobs/comm/xmpp/rpc.py`, `urn:pyobs:rpc:1`.

XEP-0009 (Jabber-RPC) framing is kept — IQ request/response, `<methodCall>`, `<methodResponse>`, `<params>`, `<param>`, `<value>`, `<fault>` all stay unchanged and remain in the `jabber:iq:rpc` namespace. What changes is the content inside `<value>`: XML-RPC's type system (`<double>`, `<boolean>`, `<struct>`, `<array>`, ...) is replaced with pyobs-namespaced XML using the same type vocabulary and serializer already built for state. `urn:pyobs:rpc:1` scopes only the content elements inside `<value>` — never the envelope.

**Namespace:** `urn:pyobs:rpc:1` — hard cutover, no transition. pyobs is a closed ecosystem; all clients are pyobs modules.

**Arguments** — one `<pyobs:value>` per `<param>`, with one child element per parameter named after it:

```xml
<!-- set_setpoint(value: float) -->
<param><value>
  <pyobs:value xmlns:pyobs="urn:pyobs:rpc:1">
    <value>-20.0</value>
  </pyobs:value>
</value></param>

<!-- take_image(exposure_time: float, image_type: ImageType) -->
<param><value>
  <pyobs:value xmlns:pyobs="urn:pyobs:rpc:1">
    <exposure_time>30.0</exposure_time>
    <image_type>object</image_type>
  </pyobs:value>
</value></param>
```

**Return value** — same `<pyobs:value>` wrapper; `Proxy` reads `inspect.signature(method).return_annotation` to know what type to deserialize into. The type information is already in the interface definition, so nothing extra needs to cross the wire. Void return is an empty `<params/>`.

```xml
<!-- return value: CoolingState -->
<params><param><value>
  <pyobs:value xmlns:pyobs="urn:pyobs:rpc:1">
    <enabled>true</enabled>
    <setpoint>-20.0</setpoint>
    <power>87.3</power>
    <time>2026-06-23T12:14:00.000</time>
  </pyobs:value>
</value></param></params>
```

External clients (web GUIs, other language bindings) use the method signatures from discovery to know what type to expect — the same disco#info schema already designed above.

**Exceptions** — `<fault>` wrapper kept inside `<methodResponse>`, IQ type stays `result` (not `error` — that's reserved for XMPP-level failures). XML-RPC `faultCode`/`faultString` content replaced with `<pyobs:fault>` carrying `<exception>` (class name) and `<message>`, so the proxy can reconstruct the right Python exception type:

```xml
<iq type="result">
  <query xmlns="jabber:iq:rpc">
    <methodResponse>
      <fault xmlns="jabber:iq:rpc">
        <value>
          <pyobs:fault xmlns:pyobs="urn:pyobs:rpc:1">
            <exception>ValueError</exception>
            <message>Target below horizon</message>
          </pyobs:fault>
        </value>
      </fault>
    </methodResponse>
  </query>
</iq>
```

**Serializer reuse** — `_dataclass_to_xml`/`_xml_to_dataclass` handle arguments and return values using the same dispatch chain already built for state (`bool`, `int`, `float`, `str`, `StrEnum`, `Time`, `list[dataclass]`, `None`). For scalar arguments, a plain parameter dict `{name: value}` + type hints from the method signature is treated as a synthetic dataclass — `zip(param_names, param_types)` replaces `dataclasses.fields()` for that case.

### Type Vocabulary

Once interface information is exposed over XMPP and consumed by non-Python clients, it effectively becomes a protocol — and should be treated as one. Concretely, this means **not** publishing raw Python type names like `float` over the wire for parameter, return, and field types. (The interface identifier itself — `ICamera` — is a different thing: it's a stable contract name, the protocol's equivalent of a service identifier, not a marshaled value, so there's no reason to translate it into something else.) Instead, define a versioned, language-neutral namespace with a fixed type vocabulary for the values that actually cross the wire:

```
urn:pyobs:interface:ICamera:2

bool
int32
float64
string
enum(CameraStatus)
array<T>
struct<...>
map<string, T>
optional<T>
datetime
```

Under this model, the Python interfaces become *one binding* of the protocol, and the web client becomes another. This is exactly the kind of pressure that has historically pushed other projects from "shared library API" toward an explicit wire protocol — and `pyobs-web-client` is the forcing function for pyobs to do the same.

#### What the vocabulary above is actually built from

Rather than guess at this, every interface in `pyobs-core` was parsed (AST, not eyeballing) for parameter and return type annotations. Full breakdown:

| Python annotation | Occurrences | Wire type |
|---|---|---|
| `float` | 33 | `float64` |
| `None` (return) | 35 | void |
| `str` | 16 | `string` |
| `int` | 12 | `int32` |
| `bool` | 6 | `bool` |
| `list[str]` | 6 | `array<string>` |
| `str \| None` | 2 | `optional<string>` |
| `list[str] \| None` | 2 | `optional<array<string>>` |
| `dict[str, float]` | 1 | `map<string, float64>` |
| `ImageFormat`, `ImageType` | 2, 2 | `enum(Name)` |
| `ExposureStatus`, `ModuleState`, `MotionStatus`, `WeatherSensors` | 1 each | `enum(Name)` |
| `tuple[float, float]` | 9 | → dataclass (`RaDec`, `AltAz`, ...) → `struct<...>` |
| `tuple[int, int, int, int]` | 2 | → dataclass (`Window`) → `struct<...>` |
| `tuple[int, int]`, `list[tuple[int, int]]` | 1, 1 | → dataclass (`Binning`) → `struct<...>` / `array<struct<...>>` |
| `tuple[bool, float, float]` | 1 | → folds into ``CoolingState` directly |
| `tuple[int, float]`, `tuple[str, float]` | 1, 1 | → dataclass → `struct<...>` |
| `dict[str, tuple[bool, bool, bool]]` | 1 | → dataclass (`ConfigCapability`) → `map<string, struct<...>>` |
| `dict[str, Any]` | 4 | → `State` dataclass (see below) |
| `dict[str, tuple[Any, str]]` | 2 | → `State`/struct; value type still genuinely open |
| `Any` (bare, not `**kwargs`) | 2 | `IConfig` only — deliberately dynamic, separate question |
| `**kwargs: Any` | 92 | never reaches the wire — dropped before `Comm.execute()` |

Two things this surfaced that the original illustrative list didn't account for:

- **Every composite return value should be a dataclass, not a tuple.** 19 methods return a `tuple[...]`, and all 19 are return types — not a single parameter uses one. More telling: each one has a setter counterpart that already takes the same fields as separate, named parameters (`move_radec(ra, dec)` next to `get_radec() -> tuple[float, float]`). The getter throws away exactly the field names the setter relies on, leaving the caller to trust positional order from a docstring. The fix is the same one already used for `state`: turn these into small dataclasses (`RaDec`, `AltAz`, `Binning`, `Window`, ...), so getter and setter share one named type instead of the getter being a blind tuple. One of the 19, `ICooling.get_cooling() -> tuple[bool, float, float]` (enabled, setpoint, power), is essentially `CoolingState` already — once `ICooling.state` exists, that RPC method likely disappears entirely in favor of reading `.state`. Practically, this means the wire vocabulary doesn't need a separate `tuple<T1, T2, ...>` entry at all — `struct<...>` (the same introspectable, field-named concept `State` already needs) covers both, instead of maintaining two composite kinds.
- **Enums are uniformly `StrEnum`.** All six enums currently in use (`ImageType`, `ExposureStatus`, `ModuleState`, `MotionStatus`, `ImageFormat`, `WeatherSensors`) are `StrEnum`, with no exceptions, confirmed on `1.x`. The wire value is just the member's string value, project-wide, already today.

**`**kwargs: Any` is on nearly every method (92 occurrences) but never reaches the wire today.** `Proxy.execute()` binds arguments via `inspect.Signature.bind()` and only forwards `ba.args[1:]` to `Comm.execute()`; `**kwargs` content lands in `ba.kwargs`, which is dropped. So despite being syntactically universal, it doesn't actually cross the RPC boundary as currently implemented — meaning the vocabulary doesn't need an `Any`/wildcard escape hatch for parameters, and that's already true, not just a goal.

**Seven return/parameter types use genuine, undocumented `Any` across six interfaces — these are the real open item, not the vocabulary itself.** `IWeather.get_weather_status`/`get_current_weather`, `IAutoFocus.auto_focus_status`, `IAcquisition.acquire_target` return `dict[str, Any]`; `IFitsHeaderBefore`/`After` return `dict[str, tuple[Any, str]]` (FITS keyword → (value, comment)). Most of these don't need a closed-vocabulary representation so much as a real schema — `get_current_weather`'s docstring already describes time/good/per-sensor fields that just haven't been turned into a `State` dataclass yet, exactly the pattern this document already proposes for `ITemperatures`.

`IConfig.get_config_value() -> Any` / `set_config_value(value: Any)` are a different case, not a fifth instance of the same problem: a generic config system is *legitimately* dynamic — any config key can hold a different type — so this isn't "should have been typed and wasn't," it's an actual escape hatch the protocol needs to account for deliberately, separately from the other six.

`datetime` is kept in the vocabulary even though nothing in current interface signatures uses it — not even the buried "time" entry inside `get_current_weather`'s untyped dict — because that's exactly the field a real `IWeather.State` would need once it exists. Reserved for when state schemas need it, not because anything requires it today.

✅ **The predicted conversion mostly happened, now further still.** Of the 19 `tuple[...]`-returning methods this survey found, only 1 remains on `develop`: `IFlatField.flat_field` (`-> tuple[int, float]`) — the rest were converted to named dataclasses as designed. Most recently: `IAutoFocus.auto_focus`, which now returns `AutoFocusResult(focus, focus_err)` instead of a bare tuple, alongside a new `IAutoFocus.state = AutoFocusState` and removal of the old `auto_focus_status() -> dict[str, Any]` method entirely; and `IWeather.get_sensor_value`, which now returns `WeatherSensorReading(sensor, value, unit, time)` instead of `tuple[str, float]`, kept as RPC by design (a live per-station call) rather than folded into `IWeather.state`, which was added separately. `IFlatField.flat_field` is a genuine RPC action result, not a State candidate, so it stays out of scope for removal.

### Enums in RPC and State

✅ Premise already true (all enums are `StrEnum`). 🔵 The `<types>` disco#info block itself is not yet implemented.

The type vocabulary above includes `enum(CameraStatus)`, but an enum reference is only half the story — the set of valid values has to be declared somewhere too. Inlining the full value list at every command parameter and state field that uses it would duplicate information within a single discovery reply and make the schema harder to keep consistent.

The proposed pattern is a shared `<types>` block, defined once per *interface* and referenced by name from anywhere in that interface's own description. Scoped to the interface, not the module, for the same reason `State` is: a module's disco#info reply can contain several independent interface blocks (see the worked example below), and an interface that's usable standalone outside `pyobs-core` shouldn't have its enum definitions depend on whatever else happens to be co-located on the same module.

```xml
<pyobs:interface xmlns:pyobs="urn:pyobs:interface:IImageFormat:1" name="IImageFormat">
  <types>
    <enum name="ImageFormat">
      <value>int8</value>
      <value>int16</value>
      <value>float32</value>
      <value>float64</value>
      <value>rgb24</value>
    </enum>
  </types>

  <command name="set_image_format">
    <parameter name="format" type="enum(ImageFormat)"/>
  </command>
</pyobs:interface>
```

This keeps two properties intact:

- **Self-contained per interface, no extra round trip.** Everything a client needs for one interface — commands, state schema, and the enum types they reference — arrives in that interface's own block. There's no separate "fetch the enum definition" query, and no dependency on a sibling block in the same reply.
- **De-duplication within one interface's block.** If the same enum is used by multiple commands and/or state fields *on that interface* (e.g. `ImageFormat` on both `set_image_format` and `IImageFormat.State.format`), it's declared once in `<types>` and referenced by name everywhere else within that block, rather than repeating the value list per use site.

What it deliberately does **not** do is de-duplicate enum definitions *across* interfaces — two interfaces on the same module that happen to use the same enum, or two different modules entirely, each carry their own copy of it. This is an acceptable trade-off: most pyobs enums (image format, exposure status, and similar) are conceptually scoped to one specific interface rather than being a global vocabulary, so there's little to gain from sharing at the protocol level, and real cost to introducing a dependency between otherwise-independent interface blocks. If a genuinely cross-cutting enum did emerge — used the same way by several unrelated interfaces — it would be a candidate for promotion into the shared type vocabulary described above (alongside `float64`, `int32`, `datetime`, ...) rather than living in any one interface's `<types>` block.

### Units

✅ `Unit(StrEnum)` implemented in `pyobs/utils/enums.py`. 🔵 Annotation rollout in progress — 12 of ~19 applicable interface files annotated as of this pass.

`float64` doesn't distinguish degrees from radians, or Celsius from Kelvin — surfaced by the C/Java thought experiment below, where there's no human reading every field to absorb a docstring's "RA in deg."

Before designing a fix, it's worth checking whether pyobs actually *has* a units problem or just an undocumented-on-the-wire one. Every angle (RA, Dec, Alt, Az, lat/lon, rotation) is degrees — zero uses of radians anywhere. Every temperature is Celsius — zero Kelvin, zero Fahrenheit. `exposure_time` and related durations are uniformly seconds. Pressure is hPa, wind speed is km/h. There are no competing conventions to reconcile; the convention already exists, consistently, project-wide — it just isn't visible to anything that isn't a human reading Python.

That finding rules out the more general fix. A per-field wire annotation in the OPC UA style (`unit="deg"` on every `<parameter>`/`<field>`) would solve a problem pyobs doesn't have, at real cost: every field needs the attribute, every codegen tool needs to interpret it, and an annotation alone doesn't *enforce* anything — a generated Java client can still pass radians and ignore the tag. Annotation without a backing convention is documentation with extra steps.

**The fix: freeze the existing convention as a fixed table, and treat it as part of the closed vocabulary rather than a per-field concern.**

| Quantity | Canonical unit |
|---|---|
| Angle (RA, Dec, Alt, Az, lat/lon, rotation) | degrees |
| Temperature | Celsius |
| Duration | seconds |
| Percentage (power, progress) | percent |
| Pressure | hPa |
| Wind speed | km/h |

One unit per physical quantity, no exceptions, documented once alongside the type vocabulary above. A C/Java codegen tool ships this table hardcoded; `float64` is then unambiguous by construction everywhere it appears, without the wire format needing to carry anything extra per field.

To get this onto the wire without hand-maintaining a second source of truth, the table is attached at the Python signature level via `typing.Annotated`. There's no existing `Unit` enum in `pyobs-core` to reference — this is new, and it belongs in `pyobs/utils/enums.py`, alongside `ModuleState`, `ExposureStatus`, `ImageType`, and the rest, following the exact same pattern already established there (`StrEnum`, one member per concept, lowercase string value, a docstring `Attributes:` block, added to that module's `__all__`):

```python
class Unit(StrEnum):
    """Enumerator for canonical physical units used on the wire.

    Attributes:
        DEGREES: Angle, in degrees.
        CELSIUS: Temperature, in degrees Celsius.
        SECONDS: Duration, in seconds.
        PERCENT: Percentage, 0-100.
        HPA: Pressure, in hectopascals.
        KM_PER_HOUR: Speed, in kilometers per hour.
    """

    DEGREES = "deg"
    CELSIUS = "celsius"
    SECONDS = "seconds"
    PERCENT = "percent"
    HPA = "hpa"
    KM_PER_HOUR = "km/h"
```

Usage on an existing signature, e.g. `IPointingRaDec.move_radec`: `ra: Annotated[float, Unit.DEGREES]`. This is fully backward compatible — `Annotated[float, X]` *is* `float` at runtime, so every existing call site keeps working untouched — and it's introspectable with `typing.get_type_hints(method, include_extras=True)`, the same mechanism already driving the type-vocabulary survey above and `Proxy`'s argument marshaling. The disco#info generator reads it and can optionally emit an advisory `unit="deg"` attribute automatically — for codegen doc-comments and generic-console field labels, not as a second hand-maintained schema. Adoption is additive: existing signatures work unannotated today and pick up `Annotated[float, Unit.X]` incrementally, the same migration shape already used for `Interface.version`.

**Should `Unit` be grounded in `astropy.units` rather than plain strings, given `pyobs-core` already depends on astropy?** Checked rather than assumed: `astropy.units` is already imported in 36 files across `pyobs-core` — but every real usage is `u.deg`/`u.degree`/`u.arcsec`/`u.arcmin` (angles) or `u.second`/`u.hour`/`u.minute`/`u.day` (time), used internally to construct `SkyCoord`/`Time`/`TimeDelta` objects at the point a module actually needs astropy machinery. Public interface signatures stay plain `float` throughout — none of the 36 files expose a `Quantity` at an interface boundary, matching what the type-vocabulary survey already found. There is zero existing usage of `u.deg_C` anywhere — temperature is handled today as plain Celsius floats, with no astropy involvement at all; "we already use astropy" is true for angles and time, not (yet) for temperature, pressure, or wind speed.

That existing pattern argues against two tempting alternatives: replacing `float` parameters with `astropy.units.Quantity` at the interface level (a much larger, riskier change than this document's scope, and a reversal of the project's established float-at-the-boundary convention), and using raw `astropy.units.Unit` objects as the `Annotated` metadata itself (astropy's unit algebra is open — `u.m / u.s**2` is just as valid as `u.deg` — which would quietly reopen the door this design is trying to close; the entire point of `Unit` being a six-member `StrEnum` is that the type checker only offers the canonical six, not "anything astropy can express").

What *is* worth taking from astropy is a conversion bridge, since 36 files already do `value * u.deg`-style construction and shouldn't have to hardcode the same unit a second time once `Unit` exists:

```python
_ASTROPY_UNITS: dict["Unit", u.UnitBase] = {
    Unit.DEGREES: u.deg,
    Unit.CELSIUS: u.deg_C,
    Unit.SECONDS: u.s,
    Unit.PERCENT: u.percent,
    Unit.HPA: u.hPa,
    Unit.KM_PER_HOUR: u.km / u.h,
}


class Unit(StrEnum):
    ...  # as above

    def to_astropy(self) -> u.UnitBase:
        """The equivalent astropy.units unit, for code that needs to build a Quantity."""
        return _ASTROPY_UNITS[self]
```

So `ra * Unit.DEGREES.to_astropy()` replaces `ra * u.deg` wherever a module is already doing that construction, without inventing a second, disconnected unit vocabulary that could drift from what astropy actually means by `"deg"`. One real wrinkle worth flagging for whoever eventually uses this for conversion, not just construction: astropy treats `deg_C` as a non-multiplicative unit — `(20 * u.deg_C).to(u.K)` raises `UnitConversionError` unless called with `equivalencies=u.temperature()`. Doesn't affect the tagging design here, but would bite silently if `to_astropy()`'s result were later fed into naive `.to()` conversion code without that equivalency.

One thing this surfaced rather than fixed: `WeatherSensors.RAIN` is a 0/1 flag encoded as `float` — not a physical quantity with a unit at all, a `bool` wearing a `float`'s clothes. Annotating it with a unit would paper over the real issue. 🔵 **Still unfixed now that `IWeather.state = WeatherState` exists**: `WeatherSensorReading.unit` for `RAIN` is just `""` (see `SENSOR_UNITS` in `weather.py`) — a placeholder, not a real answer to what this field should be.

**Optional convenience: automating the `to_astropy()` call itself, not just providing it.** Manually writing `ra * Unit.DEGREES.to_astropy()` repeats a unit that's already declared once, on the interface signature — the same kind of duplication this whole document has otherwise tried to design out. Since the unit only ever needs to be looked up, not re-specified, that lookup can be automated with a decorator on the concrete implementation:

```python
def _interface_unit_hints(cls: type, method_name: str) -> dict[str, Unit]:
    """Unit annotations from wherever this method is still @abstractmethod in the
    MRO -- unambiguously the interface declaration, never a concrete override
    (a class can't stay abstract once every method is implemented)."""
    for base in cls.__mro__:
        member = base.__dict__.get(method_name)
        if member is not None and getattr(member, "__isabstractmethod__", False):
            hints = get_type_hints(member, include_extras=True)
            return {name: u for name, hint in hints.items() if (u := _extract_unit(hint))}
    return {}


def with_units(func):
    """Converts float arguments into astropy Quantities before the wrapped method
    runs, using the Unit declared on the interface method this implements -- the
    concrete override doesn't need to repeat the annotation."""

    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        units = _interface_unit_hints(type(self), func.__name__)
        bound = inspect.signature(func).bind(self, *args, **kwargs)
        bound.apply_defaults()
        for name, unit in units.items():
            if name in bound.arguments:
                bound.arguments[name] = bound.arguments[name] * unit.to_astropy()
        return await func(*bound.args, **bound.kwargs)

    return wrapper
```

```python
class Telescope(BaseTelescope):
    @with_units
    async def move_radec(self, ra, dec) -> None:
        # ra, dec arrive as Quantity here -- Unit.DEGREES came from IPointingRaDec's
        # declaration, not from anything repeated in this method
        self._telescope.move_ra_dec(SkyCoord(ra=ra, dec=dec, frame="icrs"))
```

Deliberately stops at opt-in, not automatic for every method on every module (e.g. via `__init_subclass__`/metaclass wrapping), for three reasons: most of the 92 `**kwargs`-bearing methods never touch astropy at all and shouldn't be forced to unwrap a `Quantity` they didn't ask for; implicit, invisible type transformation is exactly the kind of magic this document has otherwise avoided in favor of explicit mechanisms (`Comm.set_state()` over auto-detection, `async with` over implicit cleanup); and an automatically-`Quantity`'d value that later gets passed on to another module's RPC call would need unwrapping again before re-serialization, which is easy to get right when it's one visible decorator and easy to get subtly wrong if it's invisible everywhere.

🔵 Not implemented — `with_units`/`_interface_unit_hints` don't exist in `pyobs-core` yet. Flagged here as still optional, not a gap.

### Versioning

✅ `Interface.version`/`Event.version` implemented; interface disco#info features versioned. 🔵 Event disco#info features and PubSub node paths for events are not yet.

Where the version number actually lives: everything above settled the *shape* of versioned namespaces (`urn:pyobs:interface:ICamera:2`, with state and PubSub node paths inheriting the same number) but not where that number actually comes from. On `1.x` — the baseline this document describes and migrates from — nothing in `Interface` carries a version at all, so there's nowhere for a developer to even put a bump. (`develop` already has exactly this added, confirming the direction independently of this document.)

Deciding whether a given change is breaking is unavoidably a developer judgment call — a field doesn't automate that away. What an explicit field *does* fix is making that one judgment call land in exactly one place, instead of needing to be threaded by hand through however many derived identifiers depend on it (interface namespace, state namespace, PubSub node path, disco#info attributes).

Given the "one versioned contract" decision already made — state inherits the interface's version rather than carrying its own — the field belongs on the interface only, **not on both**. Putting a second version field on the `State` dataclass would reintroduce exactly the problem just eliminated: two numbers that have to be kept in sync by hand, with nothing enforcing that they actually match.

```python
@dataclass
class CoolingState:
    enabled: bool
    setpoint: Annotated[float, Unit.CELSIUS]
    power: float
    time: Time = field(default_factory=Time.now)

class ICooling(Interface):
    version: int = 1
    state = CoolingState

    async def set_enabled(self, enabled: bool) -> None: ...
    async def set_setpoint(self, value: float) -> None: ...
```

`Interface.version` defaults to `1` (lowercase — matching the field name already landed on `develop`), so every interface that exists today is implicitly version 1 without anyone needing to touch it — additive, no forced migration on day one. `Interface` also declares `state: ClassVar[type | None] = None` and `capabilities: ClassVar[type | None] = None`; interfaces set either, neither, or both to their standalone dataclass, interfaces that don't inherit the `None` default, and the framework reads `interface.state`/`interface.capabilities` uniformly without `getattr` fallbacks.

The nested-`State`-class approach was considered (neater co-location, no explicit `state = SomeState` line) but rejected: when a module class inherits from multiple state-bearing interfaces — `class MyCamera(ICooling, IExposure, IFilters, Module)` — Python/mypy raises `Field 'State' has inconsistent types inherited from multiple base classes`, which is unfixable without suppressing it on every module class. Multiple inheritance is fundamental to how pyobs modules are composed, so the `ClassVar[type | None] = None` default on `Interface` is the correct design: all base classes agree on the type, individual interfaces just override the value.

**`state` and `capabilities` stay two independent ClassVars rather than one merged mechanism.** A merge was considered — one accessor, module authors never need to know which bucket a value belongs in — but `IWindow` (below) proves they're genuinely independent: it has *both* a live `window` (changes whenever `set_window` is called, delivered via PubSub subscription) and a fixed `full_frame` (set once, parsed synchronously from disco#info, never subscribed, never updated). A single ClassVar can't hold two independently-sourced dataclasses for one interface. The two mechanisms also have different delivery cost and lifecycle — collapsing them would mean every capability carries PubSub subscription machinery (server-side subscription, teardown path, "what if it updates" handling) for something that structurally cannot change, and consumers would lose the "use immediately" vs. "subscribe and wait" distinction that the split makes explicit. `Proxy.state(interface)` and `Proxy.capabilities(interface)` stay fully separate methods reading fully separate dicts — see [`Proxy`](#proxy-state-hidden-behind-update_state-and-a-state-method) below.

```python
from typing import ClassVar

class Interface:
    version: int = 1
    state: ClassVar[type | None] = None
    capabilities: ClassVar[type | None] = None
```

The XMPP layer reads `ICooling.version` once and derives every identifier that needs it from that single number: `urn:pyobs:interface:ICooling:{version}`, `urn:pyobs:state:ICooling:{version}`, and the PubSub node `.../state/ICooling/{version}`. A developer makes exactly one edit — bump `version = 2` on the interface — when they judge a change to be breaking; everything downstream that depends on it is mechanical from there.

This doesn't define what counts as breaking, deliberately — that's a developer judgment call every time, not a rule the protocol tries to encode or enforce. The field just gives that judgment call exactly one place to land instead of zero or several.

### Thought experiment: a client in a fixed-type language (C/Java)

Everything so far has been validated against a Python server, a Python proxy abstraction, and a TypeScript/JS client — all dynamically typed, or typed loosely enough to paper over gaps. Worth stress-testing the design against a statically-typed client, even hypothetically, since it surfaces real things the other two consumers have been able to ignore.

**The core mismatch isn't the wire format, it's `Proxy` itself.** `Proxy.__init__` synthesizes a brand-new Python class at runtime — `self.__class__ = cls.__class__("Proxy", tuple([cls] + interfaces), {})` — mixing in whatever interfaces the remote module happens to support, discovered live via disco#info. There's no equivalent in C, and while Java's `java.lang.reflect.Proxy` could technically fake it, nobody writing a real Java client wants a dynamically-synthesized interface implementation discovered at runtime — they want `ICamera camera = manager.get("camera", ICamera.class)` with `ICamera` a real, compile-time-known Java interface.

**The realistic answer is codegen, not runtime introspection** — the same split gRPC, D-Bus bindings, and SOAP/WSDL clients all use: a build-time tool walks the schema and emits typed bindings, and a thin generic transport underneath handles the actual IQ/PubSub mechanics. The schema this design already produces via extended disco#info — interface name+version, typed commands, state shape, event shape, the `<types>` enum block — is already the right shape of artifact for that; it's structurally the same job `generate-interfaces.py` does for `pyobs-web-client` today, just emitting Java classes or C structs instead of a TS const.

Walking the vocabulary through that lens is where some choices age well and one gap shows up clearly:

- `bool`/`int32`/`float64`/`string` — trivial, direct primitive mapping in either language.
- `enum(Name)` — maps to a real `enum ImageType { OBJECT, BIAS, ... }` in Java, or an `enum` + lookup table in C, generated once per `<types>` declaration and shared across every method/field that references it. Only works cleanly because enums are uniformly `StrEnum` on the Python side.
- `struct<...>` — this is where converting tuple-returning methods to dataclasses pays off for more than Python ergonomics. A codegen tool can do something sane with `RaDec{ra: float64, dec: float64}` — a named type with field names to hang generated accessors off. It can't do anything sane with an anonymous `tuple[float, float]`. Avoiding raw tuples in the vocabulary was a precondition for this working at all, not just a style preference.
- `array<T>`, `map<string, T>`, `optional<T>` — straightforward in Java (`List<T>`, `Map<String,T>`, `Optional<T>`). C is the genuinely awkward one: no native map or optional, so codegen has to invent a convention (key/value struct arrays; a `bool has_x` flag next to `T x`).
- `datetime` — Java has `Instant`. C has nothing, needs a generated wrapper — mirroring exactly why `pyobs.utils.time.Time` exists as a deliberate wrapper around `astropy.time.Time` on the Python side rather than using the latter directly.

**One real gap this exposes: units aren't part of the vocabulary at all.** `float64` doesn't say whether a value is degrees, radians, or Celsius — today that lives only in docstrings ("RA in deg"), which a human reading Python absorbs but a codegen tool can't enforce or even surface beyond a comment. This hasn't bitten the JS client because its Shell view is a generic console with a human reading every field anyway. A generated Java/C binding calling `telescope.moveRaDec(...)` would have no compile-time guard against radians where degrees are expected. See [Units](#units) above for the resolution.

State and events translate more cleanly than RPC does. `.../state/ICooling/{version}` PubSub subscription and "deliver the last item on subscribe" are plain XMPP semantics, not Python-specific, and mature XMPP libraries exist for both Java (Smack) and C (libstrophe, same lineage as the Strophe.js already used by `pyobs-web-client`).

## Impact Analysis

A key design goal is that these changes should be **mostly isolated to the XMPP communication layer** (`pyobs.comm.xmpp`), leaving module implementations and other `Comm` backends largely untouched.

**Correction from the original draft: `pyobs-core` has no D-Bus `Comm` backend.** `pyobs/comm/` contains only `xmpp`, `local`, and `dummy` — D-Bus was analyzed here as a plausible future backend given how closely its native introspection/properties/signals map onto this design, not as an existing one. The analysis is left below since the reasoning still holds if a D-Bus backend is ever built, but there is nothing to migrate today; treat it as speculative, not a tracked work item.

```
ICamera / ICooling / IModule        ← core interfaces: define what exists
        ↑
   Comm layer (XMPP / Local / Dummy) ← defines how it is transported
        ↑
   transport + serialization
```

| Feature | Where the work is |
|---|---|
| Publish method signatures | ~95% XMPP layer |
| Publish event schemas | ~95% XMPP layer |
| Interface versioning | mostly XMPP + interfaces |
| State PubSub | new core API + XMPP layer |
| Web client support | mostly solved by the above |

### By Comm backend

**XMPP backend** ✅ implemented
- Interface discovery: extended introspection lives entirely in the disco#info handling.
- RPC: no changes — `await camera.expose(10)` still becomes an IQ round-trip unchanged.
- Events: no changes to delivery; 🔵 discovery-time schema publication for events is still not done (see [Events](#4-events--unchanged-at-the-api-level)).
- State: a PubSub node per interface/module, with native XML payloads generated from the dataclass (see [Payload Encoding](#payload-encoding) and the [concrete implementation](#xmpp-backend-concrete-implementation)), pushed on update.

**D-Bus backend — hypothetical, does not exist in `pyobs-core`** (see correction above)
- Almost nothing would change — D-Bus already has native introspection XML, method signatures, and signals (its equivalent of events). D-Bus is, in some ways, already closer to the proposed model than XMPP is; pyobs interfaces could map onto D-Bus introspection nearly 1:1.
- State would map naturally onto **D-Bus properties** (or the `PropertiesChanged` signal pattern) — both are well-established, idiomatic D-Bus concepts.

**Local backend** ✅ implemented — `LocalComm` already has `_set_state`, `_subscribe_state`, `_set_capabilities`, `_set_presence`, direct in-memory, no serialization.

### The one genuine cross-backend change

Everything above is additive and mostly backend-local. The **only** concept that requires a small extension to the `Comm` abstraction itself (not just the XMPP implementation) is **state**:

```
Comm.set_state(state)
Comm.subscribe_state(interface, callback)
```

Each backend implements this differently (PubSub for XMPP, in-memory updates for Local; properties/signals if a D-Bus backend is ever built), but the abstraction itself — alongside the existing `call()`, `emit()`, `subscribe()` — needs to grow by exactly this much. ✅ Done: `Comm.set_state`/`subscribe_state`/`unsubscribe_state` exist on `develop`, exactly as sketched.

### Important constraint

Backend-specific concepts must not leak into core interfaces. Avoid:

```python
camera.publish_to_pubsub(state)  # ✗ leaks XMPP/PubSub into the interface
```

Use instead:

```python
self.set_state(ICooling, state)  # ✓ backend-agnostic
```

Leaking transport concepts into interfaces would make XMPP "special" and make other `Comm` backends awkward to support consistently.

## Implementation Sketch: State on `Comm` and `Proxy`

This section sketches the concrete API surface for the `Comm` extension introduced above — `set_state`, `subscribe_state`, and `unsubscribe_state` — and how the consumption side can be hidden entirely inside `Proxy`, so that module authors never call any of the three themselves.

### `Comm`: three new abstract methods

✅ **Implemented.**

```python
class Comm(ABC):
    # existing
    async def execute(self, client: str, method: str, annotation: dict[str, Any], *args: Any) -> Any: ...
    async def send_event(self, event: Event) -> None: ...
    async def register_event(
        self, event_class: type[Event], handler: Callable[[Event, str], Coroutine[Any, Any, bool]] | None = None
    ) -> None: ...

    # new
    async def set_state(self, interface: type[Interface], state: Any) -> None:
        """Publish this module's current state for the given interface."""

    async def subscribe_state(
        self,
        module: str,
        interface: type[Interface],
        callback: Callable[[Any], None],
    ) -> None:
        """Subscribe to state updates for `module`'s implementation of `interface`."""

    async def unsubscribe_state(
        self,
        module: str,
        interface: type[Interface],
        callback: Callable[[Any], None],
    ) -> None:
        """Tear down a previously created state subscription."""
```

- `set_state` is called by the module that *owns* the state — `self.set_state(ICooling, CoolingState(...))` — mirroring the existing `self.send_event(event)` pattern. The interface is passed explicitly alongside the state object.
- `subscribe_state` is called on the *consuming* side, scoped by module + interface, mirroring `self.proxy(module, interface)`.
- `unsubscribe_state` takes the exact same `(module, interface, callback)` triple, so `Comm` can pair it up with the matching `subscribe_state` call and tear it down precisely. Unlike the first two, it has exactly one caller: `Comm` itself, internally, from `_client_disconnected` (see Lifecycle below). It's a real abstract method every backend must implement — just not part of the module-author-facing or `Proxy`-facing surface.

Each backend maps these onto its native mechanism, exactly as outlined in [Impact Analysis](#impact-analysis):

| Backend | `set_state` | `subscribe_state` | `unsubscribe_state` |
|---|---|---|---|
| XMPP | publish to a PubSub node, e.g. `module@obs/state/ICooling/1` | PubSub subscribe; request the last published item on subscribe, so a new subscriber gets the current value immediately rather than waiting for the next change | send a PubSub unsubscribe IQ for the node — without this, repeated connect/disconnect cycles leave stale subscriptions accumulating server-side |
| D-Bus | set a D-Bus property | listen for `PropertiesChanged`, fetch the current property value on subscribe | remove the signal match rule / disconnect the signal receiver |
| Local | write to an in-memory cache | register a direct callback, fire it immediately with the current cached value if one already exists | remove the callback from the in-memory registry |

"Deliver the current value immediately on subscribe" is worth treating as a hard requirement across all three backends rather than an XMPP-specific nicety — it's what lets `Proxy.state` (below) be populated as soon as a proxy is created, instead of sitting at `None` until the next state publish happens to occur.

The PubSub node path carries the same version segment as the interface namespace, for the same reason: a subscriber learns which node to subscribe to from disco#info (`urn:pyobs:interface:ICooling:1` → node `.../state/ICooling/1`), so if a module moves to `ICooling:2` it publishes to `.../state/ICooling/2` instead. Old subscribers still pointed at `/1` simply stop receiving updates rather than receiving a payload shaped for a contract they don't understand — the same graceful-degradation property the interface namespace already gives for free.

### `Proxy`: state hidden behind `update_state` and a `state` method

✅ **Implemented, with one naming difference from this sketch.** The real `Proxy` methods are named `get_state(interface)`/`get_capabilities(interface)`, not the bare `state(interface)`/`capabilities(interface)` sketched below — otherwise the design (dict keyed by interface, `update_state`/`clear_state`, `wait_for_state` with timeout, capabilities populated synchronously at construction) matches as written.

The consuming side never touches `subscribe_state` directly. Subscription can't happen in `Proxy.__init__` — `__init__` can't be `async` and `subscribe_state` is — so it belongs at the actual construction site instead: `Proxy` only ever gets built in one place, `Comm._get_client`, which is already `async def` and already gated by exactly the cache check that means it only runs once per actual new proxy (not on every `proxy()`/`safe_proxy()` call — most of those hit the cache and never reach this code at all). `_get_client` is the async factory; no separate method or new abstraction needed.

A `Proxy` represents everything a module implements at once — the real constructor, `Proxy(self, client, interfaces)` inside `_get_client`, takes the plural `interfaces: list[type[Interface]]` (the camera example used throughout this document, `IGain` + `IImageFormat` + `ICooling`, is the normal case, not an edge case). A single `self._state` slot can't hold more than one interface's state, so it's a dict keyed by interface.

**`wait_for_state` closes the `get_*` semantic gap.** With `get_*`, callers blocked until the answer arrived over the wire. With `state(interface)`, they read from a local cache — which `_subscribe_state`'s `get_items(max_items=1)` pre-populates so it's immediately non-`None` for any module that's been running. The gap is first startup: a module that just came online and hasn't called `set_state` yet. `get_items` returns empty, `state(interface)` returns `None`, and code that assumed a value is populated hits `None`. `wait_for_state` handles this — returns immediately if state is already present, otherwise subscribes a one-shot callback and waits with a timeout. Needs a timeout since a module that genuinely hasn't published yet might never do so.

```python
class Proxy:
    def __init__(
        self,
        comm: Comm,
        client: str,
        interfaces: list[type[Interface]],
        capabilities: dict[type[Interface], Any],
    ):
        self._comm = comm
        self._client = client
        self._interfaces = interfaces
        self._state: dict[type[Interface], Any] = {}
        # populated synchronously by _get_client from the disco#info reply already
        # fetched to determine the interface list -- no separate round trip, no
        # subscription, never updated for the lifetime of this Proxy
        self._capabilities = capabilities

    def update_state(self, interface: type[Interface], state: Any) -> None:
        """Called by Comm whenever a new state arrives. Not intended to be called directly by module code."""
        self._state[interface] = state

    def clear_state(self) -> None:
        """Called by Comm on disconnect to drop stale state before the proxy is evicted."""
        self._state.clear()

    def state(self, interface: type[Interface]) -> Any | None:
        """Latest known state for the given interface, or None if nothing has arrived yet."""
        return self._state.get(interface)

    def capabilities(self, interface: type[Interface]) -> Any | None:
        """Fixed-for-lifetime capability data for the given interface, or None if the
        interface declares no capabilities. Always present immediately -- no waiting,
        no subscription, no wait_for_capabilities equivalent needed."""
        return self._capabilities.get(interface)

    async def wait_for_state(
        self, interface: type[Interface], timeout: float = 10.0
    ) -> Any:
        """Return state immediately if available, otherwise wait for the first update.

        Covers the edge case where a module has just come online and hasn't
        called set_state yet. get_items in _subscribe_state already handles
        the common case (module running, value already published) — this handles
        the remainder. Times out rather than hanging forever in case the module
        never publishes. Capabilities have no equivalent: they're guaranteed
        present the moment the Proxy exists, parsed synchronously from disco#info.
        """
        if self._state.get(interface) is not None:
            return self._state[interface]

        event = asyncio.Event()

        def _notify(state: Any) -> None:
            self._state[interface] = state
            event.set()

        await self._comm.subscribe_state(self._client, interface, _notify)
        try:
            await asyncio.wait_for(event.wait(), timeout=timeout)
        finally:
            await self._comm.unsubscribe_state(self._client, interface, _notify)

        return self._state.get(interface)

    def __getattr__(self, name: str) -> Callable[..., Awaitable[Any]]:
        # existing RPC forwarding via comm.execute(...)
        ...
```

```python
class Comm:
    async def _get_client(self, client: str) -> Module | Proxy | None:
        if client == "main":
            return self.module
        if client is None:
            return None

        if client not in self._proxies or not self._cache_proxies:
            try:
                interfaces = await self.get_interfaces(client)
            except IndexError:
                return None

            # new: parse <capability> elements for any interface that declares them,
            # synchronously from the same disco#info reply get_interfaces already fetched
            # to determine `interfaces` -- no extra round trip, never subscribed/updated
            capabilities: dict[type[Interface], Any] = {}
            for interface in interfaces:
                if interface.capabilities is not None:
                    elem = self._find_capability_block(client, interface)
                    if elem is not None:
                        capabilities[interface] = xml_to_value(elem, interface.capabilities)

            proxy = Proxy(self, client, interfaces, capabilities)

            # new: subscribe once per State-bearing interface, right after construction,
            # while still inside the already-async _get_client
            for interface in interfaces:
                if interface.state is not None:
                    await self.subscribe_state(client, interface, functools.partial(proxy.update_state, interface))

            self._proxies[client] = proxy

        return self._proxies[client]
```

Tested: a module implementing both `ICooling` and `ITemperatures` gets both subscribed exactly once at construction, both populated by the time `_get_client` returns (so "deliver the current value immediately on subscribe" still holds — by the time a caller gets the `Proxy`, every State-bearing interface on it is already populated, not just the first one), and a second `_get_client` call for the same client hits the cache and re-subscribes nothing. Capabilities are simpler to verify: since they're parsed synchronously from the same disco#info reply, they're present in `proxy._capabilities` the instant `_get_client` returns — no equivalent timing question to test.

Module code reads state synchronously, with no RPC round trip and no manual subscription bookkeeping — but now takes the interface explicitly, since a single `Proxy` can hold more than one:

```python
async with self.proxy("camera", IWindow) as camera:
    # live value, kept current via PubSub subscription
    current_window = camera.state(IWindow)

    # fixed value, parsed once from disco#info, present immediately, never re-fetched
    full_frame = camera.capabilities(IWindow)

    # commands are still RPC, exactly as before
    await camera.set_window(0, 0, 1024, 1024)
```

**`_ProxyView` was considered but rejected.** The idea: `_ProxyContext.__aenter__` returns a thin wrapper pre-scoped to the requested interface, exposing `.state` without an argument. This breaks when the requested interface inherits from other state-bearing interfaces — the proxy holds state for each of them in its `_state` dict, and a bare `.state` property has no way to know which one you want. The explicit `camera.state(ICooling)` form is the correct design — unambiguous regardless of the interface inheritance structure.

The only new visible surface for module authors is the `.state(interface)` method; everything about *how* it stays current — PubSub subscription, last-item retrieval, callback wiring — is internal to `Proxy` and `Comm`. Call sites do change, though — see the final decision below on `async with` being the only way to obtain a proxy.

### Lifecycle: piggyback on existing proxy eviction, no new `Proxy` API

✅ **Implemented.**

The original sketch above proposed an explicit `Proxy.close()` (or turning `Proxy` into an async context manager) to tear down its state subscription. Both would require touching every call site that currently does `camera = await self.proxy("camera", ICooling)`, since module authors would suddenly need to remember to close or `async with` something they previously just held onto.

Checking the actual `Comm`/`Proxy` implementation in pyobs-core shows this isn't necessary. Two things already exist:

- `Comm` already caches one `Proxy` per client name (`self._proxies: dict[str, Proxy]`), reused across repeated `self.proxy(...)` calls.
- `Comm` already listens for `ModuleClosedEvent` and evicts the cached proxy in `_client_disconnected` when the *remote* module disconnects — and both the XMPP and D-Bus backends already emit that event on disconnect.

In other words, proxy lifecycle is already owned by `Comm`, tied to the remote module's connection state, not to the calling code's local scope — which is exactly the assumption both `close()` and `async with` would have broken. State-subscription teardown can ride on that same existing hook. `unsubscribe_state` (above) is the method that does the actual teardown; `Comm` just needs to remember which `(interface, callback)` pairs belong to which client so it knows what to call when that client disconnects:

```python
class Comm:
    def __init__(self, ...):
        ...
        self._proxies: dict[str, Proxy] = {}
        self._state_subscriptions: dict[str, list[tuple[type[Interface], Callable[[Any], None]]]] = {}

    async def subscribe_state(
        self, module: str, interface: type[Interface], callback: Callable[[Any], None]
    ) -> None:
        # ... backend-specific subscribe ...
        self._state_subscriptions.setdefault(module, []).append((interface, callback))

    async def _client_disconnected(self, event: Event, sender: str) -> bool:
        # existing: evict the cached proxy
        if sender in self._proxies:
            self._proxies[sender].clear_state()  # drop stale state before eviction
            del self._proxies[sender]

        # new: tear down any state subscriptions held for that client
        for interface, callback in self._state_subscriptions.pop(sender, []):
            await self.unsubscribe_state(sender, interface, callback)

        return True
```

`Proxy` stays simple from the consuming side's point of view — `subscribe_state` gets called once per State-bearing interface (`Comm._get_client` does the calling, not `Proxy.__init__`), and `Proxy` never calls `unsubscribe_state` itself, directly or indirectly. `Comm`'s abstract surface grows by three methods (`set_state`, `subscribe_state`, `unsubscribe_state`), each backend has to implement all three, and `Comm._client_disconnected` gets a few new lines. What stays at zero is `Proxy`'s public surface and every existing `self.proxy(...)` call site.

**`cache_proxies` was real on `1.x`, already removed on `develop`** — `Comm.__init__()` takes no parameters there, the conditional is just `if client not in self._proxies:`, matching this document's Phase 0 direction. ✅ **Update from later in this pass: the rest of this paragraph, as originally written, is now out of date.** It previously said none of the `State`/`Comm` work or the `async with`-only `Proxy` redesign existed yet on any branch — checked directly against `develop` during this revision, and all of it is there now: `Comm.set_state`/`subscribe_state`/`unsubscribe_state`, `Proxy.get_state`/`get_capabilities`/`wait_for_state`, `_ProxyContext`-based `proxy()`/`safe_proxy()` with `has_proxy()`, and interface-feature versioning (🔵 event-feature versioning is the one piece still open — see [Versioning](#versioning) and the Work Plan).

### Reconnect with a different interface set

✅ Disconnect/reconnect handling implemented. 🔵 The stale-reference `callback(None)` refinement below is not.

Tracing the actual disconnect/reconnect chain in the XMPP backend shows this is already handled by composing two existing mechanisms, with no new code needed beyond what's sketched above:

- **Disconnect:** XMPP presence `unavailable` clears the backend's interface cache and fires `ModuleClosedEvent`, which `Comm._client_disconnected` already handles by evicting the cached `Proxy` — and, with the addition above, tearing down its state subscriptions.
- **Reconnect:** XMPP presence `available` triggers a fresh disco#info query — interfaces are re-fetched from scratch, not diffed against the old set.
- The next `self.proxy("camera", ICooling)` call after that sees the client missing from `self._proxies` (it was evicted) and builds a **brand new `Proxy`** from whatever the module advertises *now*. A dropped interface is simply absent from the new proxy's base classes; a newly added one is picked up automatically; state subscriptions wire up fresh against the current interface set.

So a module that disconnects and reconnects with a different capability set resolves correctly the next time it's looked up — no migration or diffing logic required.

**The residual gotcha is stale references, not stale lookups.** If module code holds onto a `Proxy` instance across a reconnect — `camera = await self.proxy(...)` once, kept in a long-lived task — instead of re-resolving it via `self.proxy(...)` each time it's needed, that object becomes orphaned: it's no longer in `self._proxies`, and its subscription was already torn down. RPC calls through it still fail loudly, since `execute()` always issues a fresh network call and raises `RemoteError`/`RemoteTimeoutError` if the target is gone — but `.state` would just silently freeze at its last known value, with no signal that anything changed.

The fix is small: have `unsubscribe_state`'s teardown push one final `callback(None)` before discarding it. For `Proxy.update_state`, that means an orphaned proxy's `.state` collapses to `None` — an explicit "I don't know anymore" — instead of quietly going stale. This costs nothing on the `subscribe_state` side and only touches the teardown path already being added.

🔵 **Not implemented.** `XmppComm._unsubscribe_state` on `develop` removes the callback and (on last-subscriber) sends the PubSub unsubscribe IQ, but does not push a final `callback(None)`. A `Proxy` held past its module's disconnect currently keeps returning its last-known state rather than collapsing to `None` — the gap this paragraph describes is real and still open, not yet a solved edge case.

### Final decision: `async with` only — `await self.proxy()` is removed

✅ **Implemented**, including `has_proxy()` and the `ProxyType`/`_ProxyContext` consolidation into `proxy.py`.

The dual-mode design above (`await` *or* `async with`, kept for backward compatibility) was a reasonable middle ground, but it leaves the actual problem optional: module code can still hold a long-lived `camera = await self.proxy(...)` and reintroduce the stale-reference gotcha, ambiguous `None`, and all. The decision is to commit fully: **remove the `await self.proxy(...)` form entirely. `async with` becomes the only way to obtain a proxy.**

```python
async with self.proxy("camera", ICooling) as camera:
    current_temp = camera.state(ICooling).temperature
    await camera.set_setpoint(-20)
```

This drops `__await__` from the wrapper, so plain `await self.proxy(...)` becomes a hard `TypeError` rather than something that quietly keeps working:

```python
class _ProxyContext(Generic[ProxyType]):
    """Returned by Comm.proxy() / Object.proxy() / Comm.safe_proxy(). Must be used as:
        async with self.proxy("camera", ICooling) as camera:
            ...
    """

    def __init__(self, coro: Coroutine[Any, Any, ProxyType]) -> None:
        self._coro = coro

    async def __aenter__(self) -> ProxyType:
        return await self._coro

    async def __aexit__(self, *exc_info: Any) -> None:
        # intentionally a no-op: the underlying Proxy is owned and cached
        # by Comm, not by this block, and stays alive for other callers.
        pass
```

`Generic[ProxyType]`, not bare `Any`, so `async with self.proxy("camera", ICooling) as camera:` type-checks `camera` as `ICooling`.

**Settled: `_ProxyContext` keeps the underscore, and `ProxyType` moves to `pyobs/comm/proxy.py` too.** Both live next to `Proxy` itself — `proxy.py` already only imports `Comm` under `TYPE_CHECKING`, so there's no circular-import risk. `comm.py`'s existing `from .proxy import Proxy` becomes `from .proxy import Proxy, _ProxyContext, ProxyType`, dropping its own local `ProxyType = TypeVar("ProxyType")`. `Object` in `pyobs/object.py` gets both the same way — `from pyobs.comm.proxy import _ProxyContext, ProxyType` directly from the submodule, not via `pyobs/comm/__init__.py`'s package-level re-export — and drops its own local declaration too. `1.x` currently has three independent copies of `ProxyType = TypeVar("ProxyType")` (one each in `proxy.py`, `comm.py`, `object.py`); this collapses it to one.

On the underscore specifically: the cursor-style-context-manager precedent holds (plenty of libraries return an underscore-prefixed type from a public method without it being a real problem), and the underscore still correctly communicates the one thing that actually matters — nobody is meant to construct this directly, regardless of how visible it is on hover. `pyobs/comm/__init__.py` stays at `__all__ = ["Comm", "Proxy"]` — `_ProxyContext` isn't re-exported there, consistent with the underscore meaning what it says; callers needing the type for annotation purposes import it directly from `pyobs.comm.proxy`.

What `Comm.proxy()` and `Object.proxy()` themselves look like — the existing validation/dispatch logic is untouched, just renamed to a private coroutine method and wrapped instead of awaited directly. `ProxyType` moves to `proxy.py` too, alongside `_ProxyContext` — both files that need it (`comm.py`, `object.py`) import it from there instead of each redeclaring their own `TypeVar("ProxyType")`, which is what `1.x` actually does today (checked: `comm.py` and `object.py` each currently have their own independent copy):

```python
# pyobs/comm/comm.py

from .proxy import Proxy, _ProxyContext, ProxyType  # was: from .proxy import Proxy, plus a local ProxyType = TypeVar(...)


class Comm:
    ...

    async def _resolve_proxy(
        self, name_or_object: str | object, obj_type: type[ProxyType] | None = None
    ) -> Any | ProxyType:
        """Original proxy() body, unchanged -- this is exactly what proxy() used to do
        when it was itself `async def`. Only the name and visibility changed."""
        if obj_type is not None and isinstance(name_or_object, obj_type):
            return name_or_object
        elif isinstance(name_or_object, str):
            try:
                proxy = await self._get_client(name_or_object)
            except KeyError:
                raise ValueError(f"Could not get proxy for {name_or_object}.")
            if proxy is None:
                raise ValueError(f'Could not create proxy for given name "{name_or_object}".')
            elif obj_type is None or isinstance(proxy, obj_type):
                return proxy
            else:
                raise ValueError(
                    f'Proxy obtained from given name "{name_or_object}" is not of requested type "{obj_type}".'
                )
        else:
            raise ValueError(f'Given parameter is neither a name nor an object of requested type "{obj_type}".')

    async def _safe_resolve_proxy(
        self, name_or_object: str | object, obj_type: type[ProxyType] | None = None
    ) -> Any | ProxyType | None:
        try:
            return await self._resolve_proxy(name_or_object, obj_type)
        except ValueError:
            return None

    @overload
    def proxy(self, name_or_object: str | object, obj_type: type[ProxyType]) -> _ProxyContext[ProxyType]: ...
    @overload
    def proxy(self, name_or_object: str | object, obj_type: None = None) -> _ProxyContext[Any]: ...

    def proxy(
        self, name_or_object: str | object, obj_type: type[ProxyType] | None = None
    ) -> _ProxyContext[Any]:
        """Returns a context manager; use as `async with self.proxy(...) as x:`."""
        return _ProxyContext(self._resolve_proxy(name_or_object, obj_type))

    @overload
    def safe_proxy(self, name_or_object: str | object, obj_type: type[ProxyType]) -> _ProxyContext[ProxyType | None]: ...
    @overload
    def safe_proxy(self, name_or_object: str | object, obj_type: None = None) -> _ProxyContext[Any]: ...

    def safe_proxy(
        self, name_or_object: str | object, obj_type: type[ProxyType] | None = None
    ) -> _ProxyContext[Any]:
        """Same as proxy(), but yields None inside the block instead of raising."""
        return _ProxyContext(self._safe_resolve_proxy(name_or_object, obj_type))
```

```python
# pyobs/object.py

from pyobs.comm.proxy import _ProxyContext, ProxyType  # direct from the submodule, not via pyobs.comm's __init__


class Object:
    ...

    @overload
    def proxy(self, name_or_object: str | object, obj_type: type[ProxyType]) -> _ProxyContext[ProxyType]: ...
    @overload
    def proxy(self, name_or_object: str | object, obj_type: None = None) -> _ProxyContext[Any]: ...

    def proxy(
        self, name_or_object: str | object, obj_type: type[ProxyType] | None = None
    ) -> _ProxyContext[Any]:
        """Forwards straight through -- was `return await self.comm.proxy(...)`, drop the await."""
        return self.comm.proxy(name_or_object, obj_type)
```

`safe_proxy` needed the same treatment as `proxy`, not called out elsewhere in this document until now: its current body is `return await self.proxy(...)`, which would simply break once `proxy()` stops being awaitable. It gets its own private coroutine (`_safe_resolve_proxy`, swallowing `ValueError` into `None`) rather than trying to catch the exception inside `_ProxyContext.__aenter__` itself, keeping the wrapper generic and dumb. Used the same way: `async with self.safe_proxy("camera", ICooling) as camera: if camera is not None: ...`.

**One more method worth adding while migrating call sites: `has_proxy()`, for the common case of using `proxy()` purely as an existence/type check rather than to actually obtain something to use.** A real example from migrating `pyobs-core`:

```python
try:
    device = await module.proxy(self.__follow_device, self.__follow_mode)
except ValueError:
    # cannot follow, wait a little longer
    log.warning("Cannot follow module, since it is of wrong type.")
```

If `device` gets used right there, the direct translation is just `try: / async with module.proxy(...) as device: ... / except ValueError:`, same shape as before with one extra indent level. But where the resolved proxy isn't actually needed — only the yes/no answer — forcing that through `async with ... as device: pass` would be ceremony without a purpose. The reason `proxy()`/`safe_proxy()` got forced through `async with` in the first place was specifically to stop a `Proxy` from being held across time; a pure boolean check never returns a `Proxy` to the caller at all, so that protection doesn't apply here:

```python
async def has_proxy(self, name_or_object: str | object, obj_type: type[Any] | None = None) -> bool:
    """True if a proxy of the given type can currently be resolved. Doesn't keep a reference
    to it, so doesn't need async with the way proxy()/safe_proxy() do."""
    return await self._safe_resolve_proxy(name_or_object, obj_type) is not None
```

`Object.has_proxy()` forwards the same way `Object.proxy()` does: `return await self.comm.has_proxy(name_or_object, obj_type)` (this one stays `async def` — it returns a plain `bool`, not a context manager, so there's nothing to wrap). The snippet above becomes:

```python
if not await module.has_proxy(self.__follow_device, self.__follow_mode):
    log.warning("Cannot follow module, since it is of wrong type.")
```

Tested against existing-and-right-type (`True`), existing-and-wrong-type (`False`), and nonexistent-client (`False`) — all three correctly fall out of reusing `_safe_resolve_proxy` unchanged, just reduced to a bool. `Comm` already has a `has_module` property using this exact naming convention, which is a good precedent for the name — but it's worth being clear it's not quite the same shape: `has_module` is a plain synchronous property (just checks a local attribute already in hand), where `has_proxy` necessarily has to be `async def`, since resolving a *named* proxy for the first time means actually doing interface discovery over the network, not checking something already cached.

Tested the whole chain end to end — including the import structure itself, with a faithful replica of the real package layout (`pyobs/comm/proxy.py`, `comm.py`, `__init__.py`, `object.py`) — confirming no circular import from consolidating `ProxyType`/`_ProxyContext` into `proxy.py`: `async with` resolves correctly through `Object.proxy() → Comm.proxy()`, re-entering returns the cached identical `Proxy`, an already-correct-type object passes straight through with no lookup, `safe_proxy` yields `None` inside the block on bad input instead of raising, and the old `await self.proxy(...)` form fails immediately with `TypeError` rather than silently degrading. One small, real, harmless side effect worth knowing about: because Python creates the coroutine object the moment `_resolve_proxy(...)` is called — inside `proxy()`, before any `await` happens — a stray `await self.proxy(...)` raises its `TypeError` cleanly but also leaves a `RuntimeWarning: coroutine was never awaited` as extra noise in the traceback. Doesn't break anything; just don't be alarmed by the second line.

There's a real, one-time migration cost: every existing `x = await self.proxy(...)` call site in `pyobs-core` and downstream repos needs rewriting to `async with self.proxy(...) as x:`. That's mostly mechanical — a fairly safe codemod target — though branches with early returns out of the middle of a block need manual attention since the indentation level changes.

**What replaces "hold the proxy across a long-running loop"?** Nothing was lost here, just reshaped: re-enter `async with` per iteration or per logical unit of work, which is cheap because the underlying lookup is cached:

```python
while True:
    async with self.proxy("camera", ICooling) as camera:
        if camera.state(ICooling).temperature > threshold:
            await camera.set_setpoint(-25)
    await asyncio.sleep(10)
```

It's worth being explicit that `__aenter__`/`__aexit__` here are **not** an acquire/release or connection-pool checkout — nothing is being claimed exclusively, and nothing blocks. Multiple concurrent `async with self.proxy(...)` blocks on the same client, from different tasks, are completely fine; they all resolve to the same cached `Proxy` and `__aexit__` does nothing on the way out. The context manager is purely about scoping *name resolution* to where it's used, not about owning a resource.

**Effect on the `None`-ambiguity question above:** this removes the indefinite-drift case — there's no more code path where a proxy silently goes stale for hours because someone stashed it in `self._camera` once. What remains is the narrow window *within* a single `async with` block: the module could still disconnect between `__aenter__` resolving the proxy and the line that reads `.state`. That's a much smaller window, but it isn't literally zero, so the open question itself doesn't fully close — it's just far less likely to matter in practice.

### Migration patterns from real call sites

✅ **Migration complete** — no `await self.proxy(...)` call sites remain in `pyobs-core`.

Three shapes that came up migrating actual `pyobs-core` code, beyond the single-proxy case above.

**Multiple proxies resolved in a loop.** `async with` can't appear inside a comprehension at all — it's a statement, not an expression, so `[async with p as x for p in proxies]` is a hard `SyntaxError`, not just discouraged. The deeper issue with a pattern like `states = [await p.get_motion_status() for p in proxies]` is that `proxies` itself can no longer be a list of already-resolved `Proxy` objects held across time — that's exactly the pattern being closed off. It needs to become a list of *names*, resolved and used atomically per item:

```python
async def _status(client: str) -> MotionStatus:
    async with self.proxy(client, IMotion) as p:
        return await p.get_motion_status()

states = [await _status(client) for client in clients]   # sequential, same as the original always was
states = await asyncio.gather(*(_status(client) for client in clients))   # concurrent, if actually wanted
```

The comprehension form is the literal behavior-preserving translation — `await` inside a comprehension was never concurrent, even before this redesign. `gather` (or `asyncio.TaskGroup`, since pyobs is already on 3.13/3.14) is a genuine behavior change, not required by the migration itself, but worth knowing it's there: tested at 5 simulated devices, 0.1s each, sequential took 0.5s, `gather` took 0.1s.

**A proxy that's only sometimes needed, used later in the same method.** A real shape: declare `filters: IFilters | None = None`, conditionally resolve it, then use it (or not) further down in the method body. Wrapping just the resolution line in `async with ... as filters: pass` doesn't correctly migrate this: nothing about `_ProxyContext.__aexit__` being a no-op stops `filters` from being referenced after its block has exited, so this would appear to work even though it's broken. That's a real gap in how completely this redesign "closes off" the long-held-reference pattern versus just making it more awkward to write — it discourages via friction, it doesn't enforce at runtime. The actual right tool for "maybe acquire, keep valid for the rest of the method" is `contextlib.AsyncExitStack`:

```python
from contextlib import AsyncExitStack

async def do_exposure(self) -> None:
    async with AsyncExitStack() as stack:
        filters: IFilters | None = None
        if self._filter_wheel is not None:
            log.info("Getting proxy for filter wheel...")
            filters = await stack.enter_async_context(self.safe_proxy(self._filter_wheel, IFilters))

        # ... rest of the method, however much code, filters stays valid here ...
        if filters is not None:
            await filters.set_filter("R")
```

`stack.enter_async_context(cm)` does `__aenter__()` immediately and hands back the result, but defers `__aexit__()` until the *stack* itself closes — exactly the shape needed when several conditionally-present devices (filter wheel, focuser, derotator, ...) might all be acquired this way and used together later, without nesting `async with` blocks one per device.


### XMPP backend: concrete implementation

✅ **Implemented** — see Phase 1.5 in the Work Plan for how the real `serializer.py`/`rpc.py` split differs (cleaner) from the sketch below.

**The lifecycle in one pass, before the detail below:** `set_state` publishes to a module-scoped node via XEP-0060. Incoming PubSub notifications are routed by a low-level `MatchXMLMask` handler registered directly on the XMPP client (not via slixmpp's `pubsub_publish` event, which requires plugin lazy-loading that never happens for live notifications — see below). That single handler dispatches both event and state messages: state nodes are identified by `node.startswith("pyobs:state:")` and dispatched to all registered callbacks for that node; everything else is the existing event path. `_subscribe_state` sends the ejabberd subscribe IQ only on the first subscriber for a node; subsequent calls append to the callback list without a second IQ. `_unsubscribe_state` is the mirror — removes the specific callback, sends the unsubscribe IQ only when the last callback is removed. On disconnect, `Comm._client_disconnected` calls `proxy.clear_state()` before eviction, then tears down PubSub subscriptions via `unsubscribe_state`.

How `set_state`/`subscribe_state`/`unsubscribe_state` actually become XEP-0060 calls: pyobs pins `slixmpp>=1.14.1`, and `xep_0060` (PubSub) is already registered as a plugin in `xmppclient.py` — just not yet used for anything.

**PubSub service for state nodes: `pubsub.{domain}`.** Events use XEP-0163 (PEP), which implicitly publishes to your own bare JID. State needs explicit subscribe/unsubscribe, which needs a real service JID — `pubsub.{domain}` is the standard ejabberd component automatically registered whenever `mod_pubsub` is enabled. Node auto-creation on first `publish` works with default ACLs; no explicit `create_node` call is needed.

**ejabberd deployment prerequisite.** ejabberd's built-in defaults don't enable `deliver_notifications` reliably for auto-created nodes, and `force_node_config` only applies at node creation time — `default_node_config` is the right mechanism. Any ejabberd server running pyobs 2.0 must have the following added to `/etc/ejabberd/ejabberd.yml` under `mod_pubsub`:

```yaml
mod_pubsub:
  default_node_config:
    deliver_notifications: true
    deliver_payloads: true
    persist_items: true
    max_items: 1
    send_last_published_item: on_sub_and_presence
    notify_retract: false
```

Validated end-to-end: live `CoolingState` updates through ejabberd to a Qt widget, with all integration tests passing and the full pub/sub path confirmed from `DummyCamera` through to the GUI.

**Why `MatchXMLMask` instead of `pubsub_publish`.** slixmpp's `StanzaPath` matcher — used internally by the `pubsub_publish` event — requires `msg["pubsub_event"]` to have been accessed at least once before `match()` runs, which triggers lazy plugin loading. For live notifications this never happens before matching, so `pubsub_publish` never fires. `MatchXMLMask` matches on raw XML structure and fires reliably. The handler must be synchronous (slixmpp `Callback` requirement), so `_handle_event_sync` is a thin wrapper that creates an asyncio task for the real `_handle_event`. State and event messages are distinguished by node prefix inside the same handler.

**Payload encoding: native XML generated from the dataclass, not JSON.** Payload Encoding (above) settled on native XML specifically over JSON-in-XML ("loses XML namespace/schema benefits"), generated automatically from the dataclass rather than hand-maintained per `state` class. Builds one child element per dataclass field; `_xml_to_dataclass` uses `get_type_hints(state_cls, include_extras=True)` and unwraps `Annotated[T, ...]` → `T` and `T | None` → `T` before dispatching on type, so `Annotated[float, Unit.CELSIUS]` and optional fields both round-trip correctly. `None`-valued fields are omitted from XML on serialization; absent elements deserialize back to `None`. `Time` fields serialize to ISO 8601 via `value.isot` and deserialize via `Time(child.text)`. (`from typing import Annotated, get_origin, get_args, Union` and `from pyobs.utils.time import Time` implied throughout.)

Two separate namespacing concerns that look similar but aren't the same string: the **XML namespace** is schema identity, interface-scoped only (`urn:pyobs:state:ICooling:1`, exactly matching Payload Encoding's convention) — the same for every module that implements `ICooling`. The **PubSub node path** is routing, and has to be module-scoped (`pyobs:state:{module}:ICooling:1`) precisely because `pubsub.{domain}` is one shared service across every module, unlike PEP's implicit own-JID scoping that events get for free.

```python
class StateStanza(ElementBase):
    name = "state"
    namespace = "pyobs:state"


class XmppComm(Comm):
    def __init__(self, ...):
        ...
        # existing: self._xmpp = ClientXMPP(...) and the rest of construction
        ...
        # new lines below must come after self._xmpp is constructed, not before
        self._pubsub_service = f"pubsub.{self._domain}"
        # dict[node, (interface, [callbacks])] -- list supports multiple subscribers per node
        self._state_node_handlers: dict[str, tuple[type[Interface], list[Callable[[Any], None]]]] = {}
        # MatchXMLMask fires on raw XML structure; StanzaPath (used by pubsub_publish)
        # requires lazy plugin loading that never happens for live notifications
        self._xmpp.register_handler(
            Callback("pyobs pubsub event", MatchXMLMask(...), self._handle_event_sync)
        )

    def _handle_event_sync(self, msg: Any) -> None:
        """Synchronous wrapper required by slixmpp Callback; dispatches to async handler."""
        asyncio.create_task(self._handle_event(msg))

    @staticmethod
    def _state_namespace(interface: type[Interface]) -> str:
        return f"urn:pyobs:state:{interface.__name__}:{interface.version}"

    @staticmethod
    def _state_node(module: str, interface: type[Interface]) -> str:
        return f"pyobs:state:{module}:{interface.__name__}:{interface.version}"

    @staticmethod
    def _dataclass_to_xml(state: Any, namespace: str) -> ET.Element:
        root = ET.Element(f"{{{namespace}}}state")
        for f in dataclasses.fields(state):
            value = getattr(state, f.name)
            # children are namespace-free: ET.SubElement inherits the parent namespace,
            # so use ET.Element + root.append to keep child tags as plain local names
            child = ET.Element(f.name)
            if value is None:
                continue  # omit absent optional fields from XML entirely
            if isinstance(value, bool):
                child.text = "true" if value else "false"
            elif isinstance(value, Time):
                child.text = value.isot  # ISO 8601, e.g. "2026-06-23T06:27:00.000"
            elif isinstance(value, StrEnum):
                child.text = value.value
            else:
                child.text = str(value)
            root.append(child)
        return root

    @staticmethod
    def _xml_to_dataclass(elem: ET.Element, state_cls: type) -> Any:
        hints = get_type_hints(state_cls, include_extras=True)
        ns = elem.tag[1 : elem.tag.index("}")] if elem.tag.startswith("{") else ""
        kwargs = {}
        for f in dataclasses.fields(state_cls):
            # try namespaced lookup first (our own serialization), then plain
            # (ejabberd may re-serialize without namespace on child elements)
            child = elem.find(f"{{{ns}}}{f.name}") if ns else None
            if child is None:
                child = elem.find(f.name)
            if child is None:
                kwargs[f.name] = None  # absent element → None for optional fields
                continue
            if child.text is None:
                continue
            raw_type = hints[f.name]
            # unwrap Annotated[T, ...] → T so Unit annotations don't break dispatch
            if get_origin(raw_type) is Annotated:
                field_type = get_args(raw_type)[0]
            else:
                field_type = raw_type
            # unwrap X | None → X for optional fields (get_origin returns Union)
            if get_origin(field_type) is Union:
                args = [a for a in get_args(field_type) if a is not type(None)]
                field_type = args[0] if len(args) == 1 else field_type
            if field_type is bool:
                kwargs[f.name] = child.text == "true"
            elif field_type is Time:
                kwargs[f.name] = Time(child.text)
            elif field_type is float:
                kwargs[f.name] = float(child.text)
            elif field_type is int:
                kwargs[f.name] = int(child.text)
            elif isinstance(field_type, type) and issubclass(field_type, StrEnum):
                kwargs[f.name] = field_type(child.text)
            elif field_type == int | float | str:
                # FITS value union: try int, then float, then leave as str
                try:
                    kwargs[f.name] = int(child.text)
                except ValueError:
                    try:
                        kwargs[f.name] = float(child.text)
                    except ValueError:
                        kwargs[f.name] = child.text
            else:
                kwargs[f.name] = child.text
        return state_cls(**kwargs)

    async def _set_state(self, interface: type[Interface], state: Any) -> None:
        stanza = StateStanza()
        stanza.xml = self._dataclass_to_xml(state, self._state_namespace(interface))
        node = self._state_node(self._module.name, interface)
        await self._safe_send(self.client["xep_0060"].publish, self._pubsub_service, node, payload=stanza)

    async def _subscribe_state(
        self, module: str, interface: type[Interface], callback: Callable[[Any], None]
    ) -> None:
        node = self._state_node(module, interface)

        if node in self._state_node_handlers:
            # already subscribed server-side; just append the new callback
            self._state_node_handlers[node][1].append(callback)
        else:
            # first subscriber for this node -- send the real subscribe IQ
            self._state_node_handlers[node] = (interface, [callback])
            await self._safe_send(self.client["xep_0060"].subscribe, self._pubsub_service, node)

        # deliver current value immediately regardless of whether this is the first subscriber
        try:
            result = await self._safe_send(self.client["xep_0060"].get_items, self._pubsub_service, node, max_items=1)
            item_list = result["pubsub"]["items"]["items"]
            if item_list:
                callback(self._xml_to_dataclass(item_list[0]["payload"], interface.state))
        except (slixmpp.exceptions.IqError, slixmpp.exceptions.IqTimeout):
            pass  # node exists but nothing published yet

    async def _unsubscribe_state(
        self, module: str, interface: type[Interface], callback: Callable[[Any], None]
    ) -> None:
        node = self._state_node(module, interface)
        if node not in self._state_node_handlers:
            return
        _, callbacks = self._state_node_handlers[node]
        callbacks.discard(callback) if hasattr(callbacks, "discard") else callbacks.remove(callback)
        if callbacks:
            return  # other subscribers remain; keep the server-side subscription
        del self._state_node_handlers[node]
        try:
            await self._safe_send(self.client["xep_0060"].unsubscribe, self._pubsub_service, node)
        except (slixmpp.exceptions.IqError, slixmpp.exceptions.IqTimeout):
            pass  # already gone server-side

    async def _handle_event(self, msg: Any) -> None:
        node = msg["pubsub_event"]["items"]["node"]
        if len(msg.xml.findall("{urn:sleekxmpp:delay}delay")) > 0:
            return
        if msg["from"] == self.client.boundjid.bare:
            return

        if node.startswith("pyobs:state:"):
            # state notification -- dispatch to all registered callbacks for this node
            if node not in self._state_node_handlers:
                return
            interface, callbacks = self._state_node_handlers[node]
            payload = msg["pubsub_event"]["items"]["item"]["payload"]
            state = self._xml_to_dataclass(payload, interface.state)
            for cb in callbacks:
                cb(state)
        else:
            # existing event path -- JSON payload, unchanged
            body = json.loads(xml.sax.saxutils.unescape(msg["pubsub_event"]["items"]["item"]["payload"].text))
            ...
```

The base `Comm.subscribe_state`/`unsubscribe_state` (Lifecycle, above, which already shows `self._state_subscriptions` initialized in `Comm.__init__`) get the same split `register_event`/`_register_events` already has — `subscribe_state`/`unsubscribe_state` are concrete on `Comm` (bookkeeping + call the protected method), `_subscribe_state`/`_unsubscribe_state` are no-op stubs on `Comm` that `XmppComm` overrides. `LocalComm` and `DummyComm` inherit the no-ops and need no changes:

```python
class Comm:
    def __init__(self, ...):
        ...
        self._state_subscriptions: dict[str, list[tuple[type[Interface], Callable[[Any], None]]]] = {}

    async def set_state(self, interface: type[Interface], state: Any) -> None:
        await self._set_state(interface, state)

    async def subscribe_state(self, module: str, interface: type[Interface], callback: Callable[[Any], None]) -> None:
        self._state_subscriptions.setdefault(module, []).append((interface, callback))
        await self._subscribe_state(module, interface, callback)

    async def unsubscribe_state(self, module: str, interface: type[Interface], callback: Callable[[Any], None]) -> None:
        await self._unsubscribe_state(module, interface, callback)

    async def _set_state(self, interface: type[Interface], state: Any) -> None:
        pass  # no-op; XmppComm overrides

    async def _subscribe_state(self, module: str, interface: type[Interface], callback: Callable[[Any], None]) -> None:
        pass  # no-op; XmppComm overrides

    async def _unsubscribe_state(self, module: str, interface: type[Interface], callback: Callable[[Any], None]) -> None:
        pass  # no-op; XmppComm overrides
```

Tested end-to-end against a real ejabberd server: the dataclass↔XML round-trip, the full publish → subscribe → deliver-current-value-immediately → live-update → unsubscribe control flow, and live `CoolingState` updates from `DummyCamera` through to a Qt widget. All integration tests pass.

## Summary

- The core architecture (RPC + interface discovery + events) is sound and should be retained.
- pyobs currently **underuses** XMPP: Presence and PubSub (XEP-0060) are well-suited to information pyobs currently handles with bespoke mechanisms.
- ✅ The one missing concept was **state**: continuously-published, cached, "what is true right now" data, distinct from both RPC-polled values and immutable events. Implemented for 23 of ~26 State-bearing interfaces (see the Work Plan).
- ✅ State uses **extensible, typed collections** (not fixed per-sensor fields) where hardware varies between installations — `ITemperatures.state = TemperaturesState(readings: list[SensorReading])` matches this exactly.
- ✅ Encoding leans into XMPP-native **XML**, generated automatically from dataclass schemas (`pyobs/comm/xmpp/serializer.py`) — not hand-maintained in parallel.
- Exposing interface/state/event schemas over the wire effectively turns pyobs's Python interfaces into a **language-neutral IDL**, directly enabling `pyobs-web-client` and any future non-Python bindings, and removing the need for a separate interface-extraction script. Interface/state/capability schemas are live in disco#info; 🔵 **event schema publication is not yet done** (see Events above), so the IDL is not fully complete on the wire yet.
- Almost all of this is isolated to `pyobs.comm.xmpp`; Local backend required little to no change (✅ done). There is no D-Bus backend in `pyobs-core` to migrate — see the correction in Impact Analysis.
- ✅ `await self.proxy(...)` is removed in favor of `async with self.proxy(...) as x:` as the only way to obtain a proxy, closing off the long-held-reference pattern that causes stale state at its source rather than just discouraging it. `cache_proxies` (real, on `1.x`) is gone. `has_proxy()` (plain `async def`, not `async with` — it returns `bool`, never a `Proxy`) covers the common case of using `proxy()` purely as an existence/type check. All migrated: no `await self.proxy(...)` call sites remain in `pyobs-core`.
- ✅ Versioning is settled and implemented for interfaces: `urn:pyobs:interface:ICamera:2`, with state namespaces and PubSub node paths inheriting the interface's version — commands and state are one versioned contract. `Interface.version`/`Event.version` both exist. 🔵 **Not yet done:** events are versioned independently in principle (`urn:pyobs:event:NewImageEvent:1`) but the wire side hasn't landed — event disco#info features are still the unversioned `pyobs:event:{name}` form.
- ✅ Mostly done: tuple-returning methods and undocumented `Any`-typed methods converted to named dataclasses. Only 1 of the original 19 tuple-returning methods remains (`IFlatField.flat_field`, a genuine RPC action result, out of scope for removal). `IConfig`'s deliberately dynamic config values are handled separately as designed.
- ✅ Units: `Unit(StrEnum)` exists in `pyobs/utils/enums.py` with `to_astropy()`. Annotation rollout is partial — 12 interface files use `Annotated[float, Unit.X]` so far, not yet exhaustive across every applicable field.

## Open Questions / Next Steps

Consolidated list of every 🔵 open item still standing elsewhere in this document — the single place to check what's left, rather than scanning each section.

- 🔵 **Event feature versioning + schema publication.** `add_feature` in `xmppcomm.py` still publishes the unversioned `pyobs:event:{name}` form, not `urn:pyobs:event:{name}:{version}`; no event schema block exists in disco#info yet. See [Events](#4-events--unchanged-at-the-api-level), [Versioning](#versioning), [Phase 0](#phase-0--foundations), [Phase 3](#phase-3--bulk-rollout).
- 🔵 **`<types>` disco#info block for enums** not yet implemented. See [Enums in RPC and State](#enums-in-rpc-and-state).
- 🔵 **`Unit` annotation rollout in progress** — 12 of ~19 applicable interface files annotated as of this pass. See [Units](#units).
- 🔵 **`with_units`/`_interface_unit_hints` decorator** not implemented — flagged as optional convenience, not a gap. See [Units](#units).
- 🔵 **Stale-reference `callback(None)` on disconnect not implemented.** `XmppComm._unsubscribe_state` removes the callback and sends the PubSub unsubscribe IQ on last-subscriber, but doesn't push a final `callback(None)`; a `Proxy` held past its module's disconnect keeps returning stale last-known state instead of collapsing to `None`. See [Lifecycle](#lifecycle-piggyback-on-existing-proxy-eviction-no-new-proxy-api).
- 🔵 **`IFocusModel.state = OptimalFocusState` is missing the `focus_err` field** the design (and the field's own source comment) called for — currently just `focus`/`time`. Likely an oversight worth a follow-up, not a deliberate change. See [Phase 1.5](#phase-15--rpc-payload-encoding-20).
- 🔵 **`WeatherSensors.RAIN` still has no real unit.** `WeatherSensorReading.unit` for `RAIN` is a placeholder empty string (`SENSOR_UNITS` in `weather.py`) — the underlying "0/1 flag encoded as `float`" design question flagged in [Units](#units) was never resolved, just carried through into the now-implemented `WeatherState`.
- 🔵 **`IConfig.ConfigValue` type alias** (`bool | int | float | str`) designed but never applied — `get_config_value`/`set_config_value` still type as bare `Any`. See [Appendix: State and Capability dataclass catalogue](#appendix-state-and-capability-dataclass-catalogue).
- 🔵 **`pyobs-web-client` validation and feature-string update** — external repo, not checked as part of this pass. Its live feature-matching still checks bare `pyobs:interface:`/`pyobs:event:` prefixes and needs updating to the versioned `urn:pyobs:interface:ICamera:2` / `urn:pyobs:event:ExposureFinished:1` schemes once event-feature versioning lands (`pyobs-core`'s own interface-feature side is already done). See [Phase 7](#phase-7--pyobs-web-client-catch-up).
- 🔵 **Phase 5 — `pyobs-gui`: one stale call site.** `compassmovewidget.py` still calls the removed `get_altaz()`/`get_offsets_altaz()`/`get_offsets_radec()` RPC methods on interfaces that now only expose `state =`; will raise `AttributeError` at runtime. Everything else in the repo is already migrated to `subscribe_state`/`get_capabilities`/`subscribe_presence`. See [Phase 5](#phase-5--pyobs-gui).
- 🔵 **Phase 6 — official hardware modules** status unknown, external repos, not checked as part of this pass. See [Phase 6](#phase-6--external-official-pyobs--hardware-modules).

## Work Plan

Ordered by dependency, not by section order above — several things only make sense once something earlier exists. Each phase names what it unblocks.

### Phase 0 — Foundations

✅ **Done, except event-feature versioning.** Nothing here is interesting on its own, but everything later depends on it existing first.

- ✅ `Interface.version`/`Event.version` (lowercase `version`, default `1`) — wired into state (`urn:pyobs:state:{name}:{version}`) and capabilities (`urn:pyobs:capabilities:{name}:{version}`) namespaces. **Interface features: done.** `add_feature` publishes `urn:pyobs:interface:{name}:{version}`, and `_get_interfaces`'s parsing filters to only the versioned form, so `.version` mismatches now actually exclude the interface from a resolved proxy instead of resolving silently — see the mixed-version-fleet diagnostic above. 🔵 **Still missing:** `Event` features — `add_feature(f"pyobs:event:{ev.__name__}")` still publishes the old pre-2.0 unversioned form, not `urn:pyobs:event:{name}:{version}`. See [Versioning](#versioning).
- ✅ `Comm.proxy()`/`Object.proxy()`/`Comm.safe_proxy()` converted to the `async with`-only `_ProxyContext`, `ProxyType`/`_ProxyContext` consolidated into `proxy.py`, `has_proxy()` added. Migration complete: no `await self.proxy(...)` call sites remain in `pyobs-core`. `cache_proxies` removed.
- ✅ ~~All six project enums converting `Enum` → `StrEnum`~~ Already true today — nothing to do here. This is what the wire-vocabulary's `enum(Name)` design assumes. See [Type Vocabulary](#type-vocabulary).
- ✅ mostly. `Unit(StrEnum)` added to `pyobs/utils/enums.py` with `to_astropy()`. Annotation of existing interface signatures with `Annotated[float, Unit.X]` is in progress, not exhaustive — 12 interface files use it so far. See [Units](#units).

### Phase 1 — Walking skeleton: prove State end-to-end on one interface

✅ **Done.** `ICooling` was the pilot as planned, and the pattern proved out — since generalized to 23 of ~26 State-bearing interfaces (Phase 3).

- ✅ The three `Comm` abstract methods (`set_state`, `subscribe_state`, `unsubscribe_state`) exist and are implemented for XMPP: PubSub publish/subscribe with "deliver the last item immediately" semantics, unsubscribe. See [`Comm`: three new abstract methods](#comm-three-new-abstract-methods).
- ✅ `Proxy.update_state`/`get_state(interface)`/`wait_for_state(interface)` (named `get_state`, not the bare `.state(...)` originally sketched), the auto-subscribe loop in `Comm._get_client`, and `_state_subscriptions` tracking + teardown in `_client_disconnected` are all implemented. See [`Proxy`](#proxy-state-hidden-behind-update_state-and-a-state-method) and [Lifecycle](#lifecycle-piggyback-on-existing-proxy-eviction-no-new-proxy-api).
- ✅ disco#info extended with versioned namespaces and state schema blocks; the dataclass ↔ XML auto-generation utility lives in `pyobs/comm/xmpp/serializer.py`, shared with RPC (Phase 1.5).

✅ **Validation and integration testing — implemented, mechanism differs slightly from the sketch below.** `.github/workflows/pytest-integration.yml` exists, triggered on release publish exactly as planned. Rather than an inline GitHub Actions `services:` block, it starts ejabberd via `docker compose -f tests/xmpp/docker-compose.yml up -d` and polls `docker compose ... ps` for a healthy container before running tests — same effect (a live ejabberd for `tests/integration/`), different mechanism (compose file instead of the native `services:` key). The original sketch is left below for the reasoning; the compose file itself is the source of truth for the actual container config.

```yaml
# original sketch -- actual implementation uses tests/xmpp/docker-compose.yml instead
services:
  ejabberd:
    image: ejabberd/ejabberd
    ports:
      - 5222:5222
    env:
      EJABBERD_DOMAIN: localhost
      EJABBERD_ADMIN: admin
      EJABBERD_ADMINPASS: testpassword
    options: >-
      --health-cmd "ejabberdctl status"
      --health-interval 10s
      --health-timeout 5s
      --health-retries 12
```



### Phase 1.5 — RPC payload encoding 2.0

✅ **Mostly done.**

**Landed:**
- ✅ `pyobs/comm/xmpp/serializer.py` — shared `value_to_xml`/`xml_to_value` core used by both state and RPC. Handles the full vocabulary: `bool`, `int`, `float`, `str`, `StrEnum`, `nil`, `list`, `tuple`, `dict`, dataclasses, `Annotated`/`Optional` unwrapping, ejabberd namespace-strip on round-trip. `_dataclass_to_xml`/`_xml_to_dataclass` delegate to `value_to_xml`/`xml_to_value` per field — cleaner than the document sketched.
- ✅ `pyobs/comm/xmpp/rpc.py` — `RPC` class using `urn:pyobs:rpc:1`: `params_to_xml`/`xml_to_params` for arguments, `return_to_xml`/`xml_to_return` reading `return_annotation`, `fault_to_xml`/`xml_to_fault` for typed exception reconstruction. XEP-0009 envelope (`jabber:iq:rpc`) unchanged; `urn:pyobs:rpc:1` scopes only `<value>` content.
- ✅ **`get_*` removal has gone much further than "still pending."** This isn't an intermediate step anymore for most interfaces — `ICooling.get_cooling`, `IWindow.get_full_frame`, `IModule.get_label`/`get_version`, `IMultiFiber.get_fiber_count`, `IVideo.get_video`, `IConfig.get_config_caps`, `IFocusModel.get_optimal_focus`, `IWeather.get_weather_status`/`is_weather_good`/`get_current_weather` and others are gone outright, not returning `State` as a transition shape. Only 4 `get_*`-prefixed abstract methods remain across all interfaces: `IConfig.get_config_value` (RPC by design), `IFitsHeaderBefore`/`After.get_fits_header_*` (RPC by design), and `IWeather.get_sensor_value` (RPC by design — a live per-station HTTP call, kept deliberately rather than folded into `IWeather.state`). The `IWindow.get_full_frame` vs. Discovery discrepancy this section used to flag is moot: the method isn't there to be inconsistent anymore.

🔵 **Still pending:**
- `ConfigValue = bool | int | float | str` was a settled design decision (Phase 2) but was never actually applied — `IConfig.get_config_value`/`set_config_value` still type as bare `Any` on `develop`.
- `WeatherSensors.RAIN`'s unit is still an unresolved placeholder (`""`) in `WeatherSensorReading` — see [Units](#units).

### Phase 2 — Audit and design pass (no implementation yet)

✅ **Done.**

- ✅ ~~Systematic survey of every `get_*` method across all interfaces for State-read candidacy.~~ Done — see the [get_* to State Survey](#appendix-get_-to-state-survey). All 47 methods settled: 34 `State`, 8 `Discovery`, 2 `Presence`, 4 `RPC`.
- ✅ ~~Design (not yet implement) the State dataclasses resolving the six genuinely-undocumented-`Any` interfaces.~~ Design done and now fully implemented — see the [State dataclass catalogue](#appendix-state-and-capability-dataclass-catalogue). `IAutoFocus` and `IWeather` both closed (Phase 3).
- ~~Design the tagged-union approach for `IConfig.get_config_value`/`set_config_value` separately.~~ Design settled — `ConfigValue = bool | int | float | str` — 🔵 but never actually applied in code; `get_config_value`/`set_config_value` still type as `Any` on `develop`.
- ✅ ~~Design the named dataclasses for all 19 tuple-returning methods (`RaDec`, `AltAz`, `Binning`, `Window`, and the rest).~~ Done and implemented — only 3 of the 19 remain (see [Type Vocabulary](#type-vocabulary)).

### Phase 2.5 — Discovery and Presence

✅ **Done.** These 8 methods were blocking the `get_*` removal sweep at the end of Phase 3 — done, and the sweep proceeded (see Phase 1.5/3).

**Design decisions (as implemented):**

- ✅ **`set_presence` is automatic, not explicit** — confirmed: `Module`'s `ModuleState` transitions call `Comm.set_presence` without module authors needing to call it themselves.
- ✅ **Discovery goes into the XEP-0030 disco#info handler, not a dedicated IQ handler** — `XmppComm._get_disco_info` is registered as the `xep_0030` node handler for `get_info`, exactly as decided.
- ✅ **Both Discovery and Presence implemented together.**

**Discovery (7, was 8 in the original list — `ILatLon.get_latlon` no longer exists) — all now `capabilities =`, published in disco#info `<capability>`, `get_*` method removed:**

| Method | Interface | Value | Status |
|---|---|---|---|
| `get_label()` | `IModule` | Human-readable module name | ✅ removed, `ModuleCapabilities` |
| `get_version()` | `IModule` | Software version string | ✅ removed, `ModuleCapabilities` |
| `get_fiber_count()` | `IMultiFiber` | Number of fibers (fixed hardware) | ✅ removed, `MultiFiberCapabilities` |
| `get_full_frame()` | `IWindow` | Full CCD dimensions | ✅ removed, `WindowCapabilities` |
| `get_config_caps()` | `IConfig` | Which config keys exist and are readable/writable | ✅ removed, `ConfigCapabilities` |
| `get_video()` | `IVideo` | Stream URL/path | ✅ removed, `VideoCapabilities` |

The `<capability>` element pattern designed in [Capabilities / Discovery](#1-capabilities--discovery) is implemented as described — one `<capability name="..." type="...">value</capability>` element per item, published inline in the module's disco#info response, no PubSub, no subscription. `Interface.capabilities: ClassVar[type | None] = None`, `Proxy.get_capabilities(interface)` reads a dict populated synchronously from disco#info during `_get_client`. Capabilities coverage on `develop` is actually broader than this table: `IFilters`, `IImageFormat`, `IMode`, and `IBinning` also declare `capabilities =` now (e.g. `FiltersCapabilities`, `ImageFormatCapabilities`) — additions beyond what this document originally catalogued.

**Presence (2) — module lifecycle, maps onto XMPP presence stanzas:**

| Method | Interface | Value | Status |
|---|---|---|---|
| `get_state()` | `IModule` | `ModuleState`: closed/ready/error/local | ✅ removed, `get_client_state()`/presence |
| `get_error_string()` | `IModule` | Current error message if state is error | ✅ removed, rides as `<status>` text |

✅ Implemented exactly as this section speculated it should be designed: `XmppComm._set_presence` maps `ModuleState.READY`→no `<show>`, `ERROR`→`dnd`, `LOCAL`→`away`, `CLOSED`→handled by disconnect; `error_string` rides as XMPP `<status>` text when `ERROR`.

### Phase 3 — Bulk rollout

✅ **Done**, aside from event schema publication — 🔵 see below.

- ✅ Tuple-returning methods converted to dataclasses — 18 of 19 done; the 1 remaining (`IFlatField.flat_field`) is a genuine RPC action result, out of scope for removal.
- ✅ Add `State` to every interface identified in Phase 2's `get_*` survey: **done for all ~26**. `IAutoFocus`, `IFocusModel`, and `IWeather` were the last three — all closed now (`IFocusModel`'s `state` dataclass is still missing the `focus_err` field the design called for, see Open Questions).
- ✅ disco#info and PubSub state publishing extended to every interface now carrying a `State`.
- 🔵 **Not done:** publishing `urn:pyobs:event:Name:{version}` schemas for events — event disco#info features remain unversioned (see [Events](#4-events--unchanged-at-the-api-level) and [Versioning](#versioning)), and no event schema block exists in disco#info at all yet.

### Phase 4 — Other backends and Presence

✅ Done. D-Bus not applicable (no such backend). `utils/types.py` and the old XML-RPC cast pipeline deleted.

- ~~D-Bus backend: `set_state`/`subscribe_state`/`unsubscribe_state` via D-Bus properties and `PropertiesChanged`.~~ Not applicable — `pyobs-core` has no D-Bus `Comm` backend (see the correction in [Impact Analysis](#impact-analysis)). Nothing to migrate; this bullet only applies if a D-Bus backend is built in the future.
- ✅ Local backend: `LocalComm` already implements `_set_state`, `_subscribe_state`, `_set_capabilities`, `_set_presence` as simple in-memory operations, matching this design.

### Phase 5 — `pyobs-gui`

✅ **Mostly done, checked against `../pyobs-gui` on this pass.** Every widget (`coolingwidget.py`, `filterwidget.py`, `temperatureswidget.py`, `camerawidget.py`, `focuswidget.py`, `modewidget.py`, `roofwidget.py`, `videowidget.py`, `telescopewidget.py`, `spectrographwidget.py`) now consumes `comm.subscribe_state(...)`/`comm.get_capabilities(...)`/`comm.get_interfaces(...)` and `statuswidget.py` uses `comm.subscribe_presence(...)` — the reactive 2.0 model this phase called for, not `get_*` polling.

🔵 **One leftover stale call site:** `compassmovewidget.py:45,54,58` still calls `p.get_altaz()`, `p.get_offsets_altaz()`, `p.get_offsets_radec()` (each `# type: ignore[attr-defined]`) against `IPointingAltAz`/`IOffsetsAltAz`/`IOffsetsRaDec` — all three interfaces now expose `state = AltAzState`/`AltAzOffsetState`/`RaDecOffsetState` with no `get_*` abstract method at all on `develop`. These calls will raise `AttributeError` at runtime; the widget needs migrating to `comm.get_state(...)` reads (or a live subscription) like every other widget in the repo.

### Phase 6 — External official `pyobs-*` hardware modules

🔵 Status unknown — external repos, not checked as part of this pass. Migrate the official hardware-specific repos to implement the new State interfaces — call `set_state(Interface.State(...))` wherever they currently call `set_*` or implement `get_*`. Depends on Phase 3 complete and the `get_*` removal having happened so mypy flags any missed call sites immediately. Not checked as part of this pass — these are separate repos.

Hardware module repos in scope (13):

| Repo | Hardware |
|---|---|
| `pyobs-alpaca` | ASCOM Alpaca wrapper |
| `pyobs-aravis` | Aravis webcams |
| `pyobs-asi` | ZWO ASI cameras |
| `pyobs-brot` | BROTlib telescopes |
| `pyobs-fli` | FLI cameras |
| `pyobs-flipro` | FLIPRO cameras |
| `pyobs-qhyccd` | QHYCCD cameras |
| `pyobs-sbig` | SBIG cameras |
| `pyobs-v4l` | V4L webcams |
| `pyobs-zaber` | Zaber motors |
| `pyobs-zwoeaf` | ZWO EAF focus motor |

Out of scope for this phase (infrastructure, services, UIs handled in other phases): `pyobs-core`, `pyobs-gui`, `pyobs-web-admin`, `pyobs-robotic-backend`, `pyobs-weather`, `pyobs-task-editor`, `pyobs-archive`, `pyobs-astrometry`, `pyobs-allsky-cloudcover`, `pyobs-tui`, `pyobs-launcher`, `pyobs-web`, `pyobs.github.io`.

### Phase 7 — `pyobs-web-client` catch-up

🔵 Status unknown — external repo, not checked as part of this pass. Explicitly last and lowest-priority: the client is early-stage by its own admission, was never a constraint on the design, and absorbs changes easily.

- Fix the live disco#info feature-matching to check `urn:pyobs:interface:...:{version}` / `urn:pyobs:event:...:{version}` instead of the current bare `pyobs:interface:`/`pyobs:event:` prefixes. On the `pyobs-core` side, the interface half of this is now live (see Phase 0); the event half isn't yet, since event features are still unversioned.
- Optionally retire `generate-interfaces.py`'s build-time extraction in favor of fetching schema live from disco#info, per the original motivation for this whole redesign.
- Optionally render real dropdowns for `enum`-typed parameters using the `<types>` block, replacing today's free-text inputs.

## Appendix: `get_*` to State Survey

The Phase 2 audit named above. AST-walked every interface in `pyobs-core`: 44 `get_*` methods across 29 interfaces, reviewed against your calls below.

**Camera configuration and runtime status — each interface keeps its own State, not one shared `CameraState`.** Correcting the original draft of this survey: bundling `IBinning`, `IWindow`, `IExposureTime`, `IGain`, `IFilters`, `IImageFormat`, `IImageType`, and `IExposure` into one `CameraState` assumed they're always implemented together, but they're independently usable interfaces outside `pyobs-core` too — exactly the composability the "small interfaces" philosophy ([rejected-approaches list above](#handling-state-that-isnt-fully-fixed-by-the-interface)) already commits to elsewhere in this document. A module implementing only `IGain` shouldn't be forced into a state shape carrying `filter` and `image_format` fields it has no business owning. Each interface gets its own `State`, sized to what it alone declares:

| Interface | `State` | From |
|---|---|---|
| `IBinning` | `IBinning.State` | `get_binning` |
| `IWindow` | `IWindow.State` | `get_window` (current ROI — `get_full_frame` stays Discovery, see below) |
| `IExposureTime` | `IExposureTime.State` | `get_exposure_time`, `get_exposure_time_left` |
| `IGain` | `IGain.State` | `get_gain`, `get_offset` |
| `IFilters` | `IFilters.State` | `get_filter` |
| `IImageFormat` | `IImageFormat.State` | `get_image_format` |
| `IImageType` | `IImageType.State` | `get_image_type` |
| `IExposure` | `ExposureState` | `get_exposure_status`, `get_exposure_progress` |

Combining multiple methods into one `state` is right *within* a single interface (`IExposureTime`'s two methods, `IGain`'s two) — the same pattern `ICooling.state` already uses — but not *across* interfaces. A module that genuinely implements all eight — a real camera module — ends up with eight separate state PubSub nodes instead of one, but that costs nothing: the client already has the full interface list from service discovery and knows exactly which nodes to subscribe to, the same way it already would for `ICooling` and `ITemperatures` side by side.

**Pointing / position — all drift continuously, all clear `State`, each on its own interface already:** `IPointingRaDec.get_radec` → `RaDec`, `IPointingAltAz.get_altaz` → `AltAz`, `IPointingHGS.get_hgs_lon_lat`, `IPointingHelioprojective.get_helioprojective`, `IRotation.get_rotation`, `IOffsetsRaDec.get_offsets_radec`, `IOffsetsAltAz.get_offsets_altaz`.

**Focuser:** `IFocuser.get_focus` and `IFocuser.get_focus_offset` — both `State`, on `IFocuser.State`. ✅ Implemented. `IFocusModel.get_optimal_focus` — `State`, on `IFocusModel.State(focus, focus_err)`. The 2.0 design adds `focus_err` alongside the existing `focus` value; the model recomputes continuously as conditions change, making push the right delivery mechanism. ✅ `get_optimal_focus()` removed, `IFocusModel.state = OptimalFocusState` implemented, `OptimalFocusState` now re-exported from `pyobs.interfaces` alongside `IFocusModel` (was submodule-only, inconsistent with every other state dataclass) — 🔵 but the shipped dataclass only carries `focus`/`time`; `focus_err` from the settled design was never added (see Open Questions). `FocusModel`/`AutoFocusSeries` and the `FocusSeries.get_data_points()` contract they depend on now have unit test coverage for this pass's changed surface (`tests/modules/focus/`); `get_data_points()` also now raises `NotImplementedError` by default instead of silently returning `None`, matching the rest of `FocusSeries`.

**Weather — `get_weather_status`/`is_weather_good`/`get_current_weather` folded into `IWeather.state`; `get_sensor_value` stays RPC, on reflection.** `get_weather_status` and `get_current_weather` (both already flagged as `Any`-interfaces) collapsed into `WeatherState(good, readings, time)`, with `WeatherState.readings: list[WeatherSensorReading]` (`sensor`, `value`, `unit`, `time` fields) covering the extensible-typed-collection pattern already designed for `ITemperatures` — aggregate per-sensor values only, no `station` field, since state is one value per sensor, not one per station. `get_sensor_value(station: str, sensor: WeatherSensors)` looked foldable into that same state at first glance (`sensor` is a closed `StrEnum`, not an open key the way `IConfig`'s are) but isn't: unlike the aggregate readings, it targets one specific *station* on demand — a genuine live HTTP call per invocation, not something to push continuously for every station. Kept as RPC, and changed to return `WeatherSensorReading` instead of `tuple[str, float]`, reusing the same type `WeatherState.readings` uses rather than a second one-off shape. ✅ **Implemented** — `IWeather.state = WeatherState`; `get_weather_status`/`is_weather_good`/`get_current_weather` removed outright.

**Multi-fiber, all on `IMultiFiber`:** `get_fiber`, `get_pixel_position`, `get_radius` → `State`. `get_fiber_count` → Discovery (fixed hardware count, not a live value).

**Already resolved:** `ICooling.get_cooling` and `ITemperatures.get_temperatures`, both worked out earlier in this document.

**Not state at all — static identity/capability, belongs in Discovery instead of either State or RPC:** `IModule.get_label`, `IModule.get_version`, `IMultiFiber.get_fiber_count`, `IWindow.get_full_frame`, `IConfig.get_config_caps`, `IVideo.get_video` — all fixed for the module's lifetime, all good fits for the `<capability>` element designed in [Capabilities / Discovery](#1-capabilities--discovery). ✅ Implemented, and all six `get_*` methods have been removed outright rather than just superseded. Dataclasses: `ModuleCapabilities`, `MultiFiberCapabilities`, `WindowCapabilities`, `ConfigCapabilities`, `VideoCapabilities` — see the [State and Capability dataclass catalogue](#appendix-state-and-capability-dataclass-catalogue). (`ILatLon.get_latlon`/`LatLonCapabilities`, in this bucket originally, no longer exist — `ILatLon` was removed from `pyobs.interfaces`.)

**Not State — maps onto Presence instead:** `IModule.get_state` (`ModuleState`: closed/ready/error/local) and `IModule.get_error_string`. ✅ Implemented — both methods removed, replaced by `Comm.get_client_state()`/presence subscription, exactly as this section proposed.

**Stays RPC:** `IConfig.get_config_value(name)` and `get_config_value_options(name)` — already the flagged open-key exception, still RPC as designed. `IFitsHeaderBefore`/`After.get_fits_header_*(namespaces)` — stays RPC, still present. Return type ✅ applied as `dict[str, FitsHeaderEntry]` (`FitsHeaderResult` wrapper dropped as unnecessary).

**Settled:** `IMode.get_mode(group: int)` — ✅ implemented as `IMode.state = ModeState`. `IMotion.get_motion_status(device: str | None)` — ✅ implemented as `IMotion.state = MotionState`. `IConfig.get_config_value`/`set_config_value` — stays RPC as designed, 🔵 but the `ConfigValue = bool | int | float | str` type alias was never actually added; both still type as bare `Any`.

**The `is_*` methods belong in this survey too, not as a footnote — `IReady.is_ready`, `IRunning.is_running`, `IWeather.is_weather_good` are all `State`,** each on its own interface's own state, same reasoning and same per-interface boundary as everything above. `IReady`/`IRunning`/`IWeather` ✅ all implemented — `is_weather_good()` removed, folded into `WeatherState.good`.

**Tally** (44 `get_*` methods, plus the three `is_*` methods folded in, 47 total): **34 `State`, 8 `Discovery`, 2 `Presence`, 4 stay `RPC`**. All items settled at the design level. Implementation: all 34 `State` items done (`IFocusModel` implemented but missing the `focus_err` field — see Open Questions), all 8 `Discovery` done, both `Presence` done, 3 of 4 `RPC` items match their settled type (🔵 the fourth, `IConfig`'s `ConfigValue` alias, was never applied). See the [State dataclass catalogue](#appendix-state-and-capability-dataclass-catalogue).

## Appendix: State and Capability dataclass catalogue

Every interface's state is a standalone dataclass assigned to `interface.state` — `ICooling.state = CoolingState`, etc. `Interface.state: ClassVar[type | None] = None` provides the default; all base classes agree on the type so module classes inheriting from multiple state-bearing interfaces don't cause `[inconsistent-inheritance]` errors. Supporting dataclasses used as list elements (`DeviceMotionStatus`, `SensorReading`, etc.) stay standalone since they're not `interface.state` targets themselves. `AutoFocusPoint` similarly stays standalone as a list element inside `AutoFocusState`. `AutoFocusResult` is a third, independent case — not a list element, not a `state`, but the return type of the `auto_focus()` RPC action itself, following the same `Result`-suffix convention as `AcquisitionResult`/`FitsHeaderResult` below for "RPC action returns a named dataclass instead of a bare tuple/dict."

Capabilities follow the identical pattern via a second, independent ClassVar — `Interface.capabilities: ClassVar[type | None] = None`, `IModule.capabilities = ModuleCapabilities`, etc. — covering the Discovery interfaces from the survey (`ILatLon`/`LatLonCapabilities`, listed in the survey's original count, no longer exist). Fixed-for-lifetime values, parsed once from disco#info rather than subscribed via PubSub; see [the "two independent ClassVars" note above](#proxy-state-hidden-behind-update_state-and-a-state-method) for why these stay separate from state rather than merging into one mechanism. ✅ Implemented, and broader on `develop` than this catalogue lists: `IFilters`, `IImageFormat`, `IMode`, and `IBinning` also declare `capabilities =` now (e.g. listing available filters/formats/modes/binning options) — additions made during implementation, not catalogued here in detail.

**Migration pattern for existing tuple-returning methods.** The state object becomes the module's single source of truth; the tuple-returning RPC method unpacks from it rather than maintaining separate internal variables:

```python
# one field, updated on change
self._cooling_state = CoolingState(enabled=True, setpoint=-20.0, power=87.3)
await self.comm.set_state(ICooling, self._cooling_state)

# RPC method unpacks -- no separate tracking needed
async def get_cooling(self) -> tuple[bool, float, float]:
    return self._cooling_state.enabled, self._cooling_state.setpoint, self._cooling_state.power
```

When the tuple methods are eventually removed, `_cooling_state` and `set_state` stay — only `get_cooling` goes away. For interfaces where one `State` covers multiple separate getters (`IFocuser.get_focus`/`get_focus_offset`, `IGain.get_gain`/`get_offset`), both unpack from the same object. For interfaces where the state combines fields from methods that previously updated independently (`IExposure.get_exposure_status` + `get_exposure_progress`), the module updates both fields together in one `set_state` call — which is correct anyway, since a status/progress pair written at different times is inconsistent.

```python
from dataclasses import dataclass, field
from typing import Annotated, ClassVar
from pyobs.utils.time import Time
from pyobs.utils.enums import Unit
from pyobs.interfaces.enums import (
    ExposureStatus, ImageFormat, ImageType, MotionStatus, WeatherSensors
)

# Supporting dataclasses (list elements — not interface.state targets themselves)

@dataclass
class DeviceMotionStatus:           # MotionState.devices element
    name: str
    status: MotionStatus

@dataclass
class SensorReading:                # TemperaturesState.readings element
    name: str
    value: Annotated[float, Unit.CELSIUS]

@dataclass
class WeatherSensorReading:         # WeatherState.readings element -- also get_sensor_value()'s RPC return type
    sensor: WeatherSensors
    value: float
    unit: str
    time: Time = field(default_factory=Time.now)  # get_sensor_value() parses the station's own ISO-8601 time here

@dataclass
class ModeEntry:                    # ModeState.modes element
    group: int
    mode: str

@dataclass
class AutoFocusPoint:               # AutoFocusState.points element
    focus: float
    value: float

@dataclass
class FitsHeaderEntry:              # FitsHeaderResult.entries value
    value: int | float | str        # closed FITS value type set
    comment: str


# ---- Camera configuration ----

@dataclass
class BinningState:
    x: int
    y: int
    time: Time = field(default_factory=Time.now)

@dataclass
class WindowState:                          # current ROI; get_full_frame → Discovery
    x: int
    y: int
    width: int
    height: int
    time: Time = field(default_factory=Time.now)

@dataclass
class ExposureTimeState:
    exposure_time: Annotated[float, Unit.SECONDS]
    exposure_time_left: Annotated[float, Unit.SECONDS]
    time: Time = field(default_factory=Time.now)

@dataclass
class GainState:
    gain: float
    offset: float
    time: Time = field(default_factory=Time.now)

@dataclass
class FilterState:
    filter: str
    time: Time = field(default_factory=Time.now)

@dataclass
class ImageFormatState:
    image_format: ImageFormat
    time: Time = field(default_factory=Time.now)

@dataclass
class ImageTypeState:
    image_type: ImageType
    time: Time = field(default_factory=Time.now)

@dataclass
class ExposureState:
    status: ExposureStatus
    progress: float
    time: Time = field(default_factory=Time.now)


# ---- Pointing / position ----

@dataclass
class RaDecState:
    ra: Annotated[float, Unit.DEGREES]
    dec: Annotated[float, Unit.DEGREES]
    time: Time = field(default_factory=Time.now)

@dataclass
class AltAzState:
    alt: Annotated[float, Unit.DEGREES]
    az: Annotated[float, Unit.DEGREES]
    time: Time = field(default_factory=Time.now)

@dataclass
class HGSState:
    lon: Annotated[float, Unit.DEGREES]
    lat: Annotated[float, Unit.DEGREES]
    time: Time = field(default_factory=Time.now)

@dataclass
class HelioprojectiveState:
    theta_x: Annotated[float, Unit.DEGREES]
    theta_y: Annotated[float, Unit.DEGREES]
    time: Time = field(default_factory=Time.now)

@dataclass
class RaDecOffsetState:
    ra: Annotated[float, Unit.DEGREES]
    dec: Annotated[float, Unit.DEGREES]
    time: Time = field(default_factory=Time.now)

@dataclass
class AltAzOffsetState:
    alt: Annotated[float, Unit.DEGREES]
    az: Annotated[float, Unit.DEGREES]
    time: Time = field(default_factory=Time.now)

@dataclass
class RotationState:
    rotation: Annotated[float, Unit.DEGREES]
    time: Time = field(default_factory=Time.now)


# ---- Motion / focus ----

@dataclass
class MotionState:
    status: MotionStatus
    devices: list[DeviceMotionStatus] = field(default_factory=list)
    time: Time = field(default_factory=Time.now)

@dataclass
class FocuserState:
    focus: float
    focus_offset: float
    time: Time = field(default_factory=Time.now)

@dataclass
class OptimalFocusState:            # 2.0 adds focus_err alongside the existing focus value
    focus: float
    focus_err: float                # 🔵 designed but not shipped -- develop's version has only focus/time
    time: Time = field(default_factory=Time.now)


# ---- Module / system ----

@dataclass
class ReadyState:
    ready: bool
    time: Time = field(default_factory=Time.now)

@dataclass
class RunningState:
    running: bool
    time: Time = field(default_factory=Time.now)


# ---- Sensors ----

@dataclass
class CoolingState:                 # Phase 1 reference implementation, as originally sketched
    enabled: bool
    setpoint: Annotated[float, Unit.CELSIUS]
    power: float
    time: Time = field(default_factory=Time.now)

# Actual develop shape differs: setpoint/power are Optional, power is Annotated[int,
# Unit.PERCENT] (not float), and field order is setpoint/power/enabled/time -- confirmed
# by reading pyobs/interfaces/ICooling.py directly. Representative of how the other
# dataclasses in this catalogue may also have drifted in minor ways not individually
# re-verified here; treat the interface source files as authoritative over this appendix.

@dataclass
class TemperaturesState:
    readings: list[SensorReading] = field(default_factory=list)
    time: Time = field(default_factory=Time.now)

@dataclass
class WeatherState:
    good: bool
    readings: list[WeatherSensorReading] = field(default_factory=list)
    time: Time = field(default_factory=Time.now)


# ---- Multi-fiber ----

@dataclass
class MultiFiberState:
    fiber: str
    pixel_x: float
    pixel_y: float
    radius: float
    time: Time = field(default_factory=Time.now)


# ---- Mode ----

@dataclass
class ModeState:
    modes: list[ModeEntry]
    time: Time = field(default_factory=Time.now)


# ---- Auto-focus ----

@dataclass
class AutoFocusResult:              # auto_focus() return type -- RPC action result, not state
    focus: float
    focus_err: float

@dataclass
class AutoFocusState:               # growing curve during autofocus run
    points: list[AutoFocusPoint] = field(default_factory=list)
    time: Time = field(default_factory=Time.now)


# ---- Interface.state assignments ----
# ✅ = implemented on develop with this ClassVar set (field-level shape may differ
# slightly from the dataclasses sketched above -- interface source is authoritative).
# 🔵 = not yet implemented as of this pass.

class Interface:
    state: ClassVar[type | None] = None

class IBinning(Interface):          state = BinningState        # ✅
class IWindow(Interface):           state = WindowState          # ✅
class IExposureTime(Interface):     state = ExposureTimeState    # ✅
class IGain(Interface):             state = GainState            # ✅
class IFilters(Interface):          state = FilterState          # ✅
class IImageFormat(Interface):      state = ImageFormatState     # ✅
class IImageType(Interface):        state = ImageTypeState       # ✅
class IExposure(Interface):         state = ExposureState        # ✅
class IPointingRaDec(Interface):    state = RaDecState           # ✅
class IPointingAltAz(Interface):    state = AltAzState           # ✅
class IPointingHGS(Interface):      state = HGSState             # ✅
class IPointingHelioprojective(Interface): state = HelioprojectiveState  # ✅
class IOffsetsRaDec(Interface):     state = RaDecOffsetState     # ✅
class IOffsetsAltAz(Interface):     state = AltAzOffsetState     # ✅
class IRotation(Interface):         state = RotationState        # ✅
class IMotion(Interface):           state = MotionState          # ✅
class IFocuser(Interface):          state = FocuserState         # ✅
class IFocusModel(Interface):       state = OptimalFocusState    # ✅ get_optimal_focus() removed -- 🔵 focus_err field not shipped
class IReady(Interface):            state = ReadyState           # ✅
class IRunning(Interface):          state = RunningState         # ✅
class ICooling(Interface):          state = CoolingState         # ✅
class ITemperatures(Interface):     state = TemperaturesState    # ✅
class IWeather(Interface):          state = WeatherState         # ✅ get_weather_status/is_weather_good/get_current_weather removed; get_sensor_value kept (RPC by design), returns WeatherSensorReading
class IMultiFiber(Interface):       state = MultiFiberState      # ✅
class IMode(Interface):             state = ModeState            # ✅
class IAutoFocus(Interface):        state = AutoFocusState       # ✅ auto_focus() -> AutoFocusResult; auto_focus_status() removed


# ---- Capabilities: fixed-for-lifetime values, parsed once from disco#info ----
# Separate ClassVar from state -- see the "two independent ClassVars" note above.
# IWindow is the one interface with both: a live `window` and a fixed `full_frame`.
# All of the below are ✅ implemented on develop. `ILatLon`/`LatLonCapabilities`
# (originally listed here) no longer exist -- ILatLon was removed from pyobs.interfaces.
# Also implemented but not in this original catalogue: FiltersCapabilities (IFilters),
# ImageFormatCapabilities (IImageFormat), ModeCapabilities (IMode), BinningCapabilities
# (IBinning) -- added during implementation, field shapes not audited here.

@dataclass
class ModuleCapabilities:           # IModule.get_label + get_version folded into one
    label: str
    version: str

@dataclass
class WindowCapabilities:           # IWindow.get_full_frame -- fixed CCD dimensions
    full_frame_x: int
    full_frame_y: int
    full_frame_width: int
    full_frame_height: int

@dataclass
class MultiFiberCapabilities:
    fiber_count: int

@dataclass
class ConfigCapabilities:
    caps: dict[str, tuple[bool, bool, bool]] = field(default_factory=dict)  # readable, writable, has_options

@dataclass
class VideoCapabilities:
    video: str                      # stream URL/path

class IModule(Interface):           capabilities = ModuleCapabilities
class IConfig(Interface):           capabilities = ConfigCapabilities
class IVideo(Interface):            capabilities = VideoCapabilities

# IWindow and IMultiFiber each declare both state (above, in the state assignments
# block) and capabilities -- shown separately here only because this catalogue groups
# by mechanism; in the real interface file both lines sit together in one class body:
#   class IWindow(Interface):
#       state = WindowState
#       capabilities = WindowCapabilities
#   class IMultiFiber(Interface):
#       state = MultiFiberState
#       capabilities = MultiFiberCapabilities


# ---- RPC result types (not State) ----
# IAcquisition.acquire_target -- ✅ now returns AcquisitionResult (applied).
# IFitsHeaderBefore/After.get_fits_header_* -- ✅ applied as dict[str, FitsHeaderEntry];
# FitsHeaderResult wrapper was dropped as unnecessary.

@dataclass
class AcquisitionResult:            # IAcquisition.acquire_target return type -- ✅ applied
    time: Time
    ra: Annotated[float, Unit.DEGREES]
    dec: Annotated[float, Unit.DEGREES]
    alt: Annotated[float, Unit.DEGREES]
    az: Annotated[float, Unit.DEGREES]
    # exactly one offset pair set depending on telescope capabilities;
    # None fields omitted from XML on serialization
    off_ra: Annotated[float, Unit.DEGREES] | None = None
    off_dec: Annotated[float, Unit.DEGREES] | None = None
    off_alt: Annotated[float, Unit.DEGREES] | None = None
    off_az: Annotated[float, Unit.DEGREES] | None = None


# ---- Config (dynamic, not a State -- typed alias for get/set_config_value) ----
# 🔵 Not yet applied -- get_config_value/set_config_value still type as bare Any on develop.

ConfigValue = bool | int | float | str  # closed primitive set; bool before int (subclass)
```