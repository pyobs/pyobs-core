# Design: mobile client for pyobs (Android/iOS + tablets) and the shared TypeScript client core

Status: proposed

Repos: pyobs-core (wire protocol, reference implementations), pyobs-web-client (core extraction
and refactor), pyobs-js-core (new shared-core repo + npm package, planned), pyobs-js-fits (new
FITS repo + npm package, planned), pyobs-app (new mobile app repo, planned)

Discussion thread: pyobs/pyobs-core issue #884 — this doc is the formal write-up of that
discussion; the issue keeps the decision history and stays the place to discuss. Deliberately no
implementation plan yet; the phases below sketch the order of work, a `specs/plans/` doc follows
once the spike (see Phasing) is done.

## Goal

A smartphone/tablet app for pyobs on Android and iOS that behaves like the existing clients —
`pyobs-gui`, `pyobs-web-client`, `pyobs-polaris`: log in with JID/password (plus optional server
override), discover modules live over XMPP (presence + disco#info), render interfaces generically
and schema-driven (the Polaris model), issue commands via RPC, and subscribe to state and events.
Tablets are in scope from the start (see Tablet scope). The architectural goal is that the
protocol layer is written **once, in TypeScript**, and shared with `pyobs-web-client`, so the app
is a UI + thin adapter on a core that the web client's test suite already exercises.

## Non-goals (for now)

- Desktop builds, and replacing `pyobs-polaris`/`pyobs-gui` — an open question, not a decision
  (see Open questions). Nothing here retires an existing client.
- Remote push notifications (XEP-0357 to APNs/FCM) — scoped but deferred; v1 relies on
  reconnect-on-foreground (see Open questions for the rationale that shapes the event/state
  model now).
- Any change to `pyobs-core`'s Python runtime behavior. Impact on pyobs-core is documentation of
  a new client family and a stable reference for its wire semantics.

## Context: the client ecosystem

pyobs 2.x control traffic is XMPP end-to-end (`specs/design/pyobs_2_0_wire_protocol.md`); there
is no REST/control API. Three client families exist today, split by UI stack and by transport:

| Client | Stack | XMPP transport |
|---|---|---|
| `pyobs-core`/`pyobs-gui` | Python/PySide6 + slixmpp | direct TCP c2s (5222/STARTTLS) |
| `pyobs-polaris` | C++20/Qt6/QML + QXmpp | direct TCP c2s (5222) |
| `pyobs-web-client` | Vue 3 + strophe.js | XMPP over WebSocket (RFC 7395), `ws(s)://<domain>:5280/ws` |

All meet at the same ejabberd, which routes TCP and WebSocket sessions interchangeably.
`pyobs-web-client` and `pyobs-polaris` already proved that non-Python clients can be built
"from the wire up", with no `pyobs-core` dependency — the mobile app is another member of that
family. This design changes nothing about the protocol; it adds a documented client and removes
the *duplication* between future clients (ADR 0017).

### Required protocol surface for any new client

- **Presence** — module lifecycle (online/offline, `ModuleState`).
- **XEP-0030 disco#info** — which modules exist and which interfaces (with typed schemas) they
  expose; this drives the generic, schema-rendered UI.
- **Custom XEP-0009 RPC** (`urn:pyobs:rpc:1` value/XML codec), including timeout semantics.
  Reference implementations: `pyobs-core` `pyobs/comm/xmpp/xep_0009/` (+ `xep_0009_timeout`),
  TypeScript port `pyobs-web-client` `src/pyobs-codec.ts`.
- **XEP-0060 pubsub** — per-module state streams and events (pyobs 2.0 moved events to explicit
  pubsub subscription; see ADR 0012).
- **Keepalive (XEP-0199) and reconnect**; a unique resource per install — the server kicks
  duplicate sessions (ADR 0002 conflict semantics).
- A **separate, token-authenticated HTTP channel** for image/video previews — camera frames do
  not go over XMPP (`httpfilecache`/`BaseVideo` HTTP token-auth work in `specs/plans/`).

## Decisions

Three decisions came out of the issue discussion, each recorded with its full considered-and-
rejected alternatives as an ADR:

| Decision | ADR |
|---|---|
| Transport: XMPP over WebSocket (RFC 7395) to the existing ejabberd `/ws` endpoint, not direct TCP | [ADR 0016](../adrs/0016-mobile-client-xmpp-over-websocket-not-direct-tcp.md) |
| `pyobs-web-client` and the mobile app share one framework-agnostic TypeScript core | [ADR 0017](../adrs/0017-web-and-mobile-share-framework-agnostic-ts-core.md) |
| Framework: React Native with the Expo toolchain (not Flutter or Qt/QML) | [ADR 0018](../adrs/0018-mobile-app-framework-react-native-expo.md) |

In one paragraph each:

- **Transport.** WebSocket framing (RFC 7395) over `wss://…:5280/ws` — same transport the web
  client already uses. Mobile library reality is the deciding factor: WebSocket is first-class in
  every cross-platform mobile runtime, while XMPP-over-TCP stacks are native-per-platform or
  alpha wrappers; the server needs no change; `wss:` on 443 is firewall/carrier friendly; and
  backgrounding kills TCP and WebSocket alike, so it is no argument for TCP. Direct TCP stays
  right only where the library is TCP-native and proven (the Qt/QXmpp route, native dual stack).
- **Shared TS core.** The protocol layer lives in one framework-agnostic, DOM-free TypeScript
  package — `pyobs-js-core`, kept in its own repo and published to npm — consumed by the Vue web
  app and the React Native app through thin adapters. Its FITS sibling (`pyobs-js-fits`) follows
  the same pattern: own repo, published to npm, extracted from `pyobs-web-client`. The web client's existing unit/e2e suites become the core's regression
  net before any mobile code exists; protocol behavior changes once and ships everywhere in
  lockstep.
- **Framework.** React Native + Expo — the only candidate that *shares* TypeScript with
  `pyobs-web-client`, so the ADR 0017 core is consumed rather than ported. Real native apps
  (native widgets, native WebSocket, APNs/FCM, Keychain/Keystore), not a WebView shell. Expo
  provides the managed workflow (`expo-notifications`, `expo-secure-store`, `expo prebuild`,
  EAS); tablets from the same codebase. Consequences: no first-class native Linux desktop target
  via RN (see Open questions), Metro monorepo config, FITS rendering stays per-platform.

## Architecture

Four repos, two published packages:

```
pyobs-js-core (new repo; published to npm)
└── the shared client core: codec, discovery, RPC w/ timeouts,
    pubsub subscription manager, keepalive/reconnect

pyobs-js-fits (new repo; published to npm; extracted from pyobs-web-client)
└── FITS header/image decode + canvas render — decode is platform-neutral,
    render stays web-only (subpath exports keep RN free of canvas code)

pyobs-app (new repo; the mobile client, app display name "pyobs")
└── apps/mobile               ← React Native (Expo) app: UI + thin adapter on the core

pyobs-web-client (existing repo)
├── apps/web                  ← existing Vue app, thinned to UI + thin adapter
└── packages/pyobs-fits       ← moves out to the pyobs-js-fits repo
```

`pyobs-web-client`'s `packages/pyobs-fits` workspace package is the model for this pattern — and
it moves out too: shared JS packages live in their own repos (`pyobs-js-core`, `pyobs-js-fits`),
so neither app owns the other's dependency. Both apps depend on the published npm packages;
during phase 2 (the web client's own migration onto them) a dev-time git/npm dependency bridges
the publish lag.

**Core boundary rules** (the guardrail that keeps every future client — including a desktop one —
on the same core):

- No browser DOM, no `window`, no Vue, no React Native imports. XML is built/parsed with a
  platform-neutral implementation (`@xmpp/xml`/ltx or the stanza.js family).
- UI-framework-neutral: the core emits events or owns a plain store; each app wraps it in a thin
  adapter (Vue composable today; RN hook/provider in the app).
- Platform seams behind interfaces: storage (browser storage vs Keychain/Keystore), WebSocket
  provider, URL derivation is pure logic.

### Extraction work in `pyobs-web-client`

Three browser couplings currently block sharing; removing them is a bounded refactor (details and
consequences in ADR 0017):

1. `src/pyobs-codec.ts` builds XML via the browser DOM (`document.implementation.createDocument`,
   `document.createElement`) because strophe.js serializes DOM elements — move to a
   platform-neutral XML layer; the encode/decode logic itself survives unchanged.
2. The XMPP core is strophe.js (browser-first) — swap to an RN-capable core with a WebSocket
   transport (`@xmpp/client` or stanza.js); verify the choice in the spike below.
3. `src/composables/useXmpp.ts` mixes protocol logic with Vue state (`ref`s, `sessionStorage`,
   `window.location`) — split into core + thin Vue adapter.

## Tablet scope

Phones *and* tablets from the same codebase: a universal iOS app (iPhone + iPad, including
iPadOS Split View / Stage Manager) and Android phones/tablets from the same build — Expo includes
iPad by default; there is no separate tablet project. The UI is adaptive by window-size
breakpoints (~600 dp: compact vs expanded) rather than device-specific, mirroring
`pyobs-web-client`'s existing rule that every design must work on mobile *and* desktop (its
CLAUDE.md; its specs test at 390×844 vs desktop). Layout switches per breakpoint: bottom tab bar
→ sidebar/drawer; 1–2 schema-driven card columns → 3–5; master–detail (module list + detail) on
wide screens. Same component library into different containers per breakpoint — not a code fork.
Design in dp, not pixels; treat iPad width as a continuous range, not portrait/landscape.

## Phasing

1. **Spike** (prerequisite, tracked on the issue): verify the XMPP core choice (`@xmpp/client`
   vs stanza.js) inside an Expo app on both iOS and Android against a pyobs ejabberd; validate
   the monorepo Metro configuration (`watchFolders`/`nodeModulesPaths`) with the shared package;
   confirm the Expo development loop (Expo Go / dev client).
2. **Extract the shared packages into their own repos** (`pyobs-js-core`; `pyobs-js-fits` moves
   out of the web-client workspace — this removes the three browser couplings above) and migrate
   `pyobs-web-client` onto the published packages — the web client's existing unit/e2e suites are
   the regression net (a dev-time git/npm dependency bridges the publish lag during the
   migration).
3. **Build `apps/mobile`** on the same core: v1 = login, module discovery, schema-driven
   dashboard/control (the Polaris card model), pubsub state/events, keepalive/reconnect,
   reconnect-on-foreground state catch-up, adaptive phone/tablet layouts, secure credential
   storage. Local notifications for app-scheduled reminders are app-side and in scope whenever
   wanted; remote push is not (Open questions).
4. **Deferred:** remote push (XEP-0357), desktop route decision (Open questions).

## Open questions

Resolved while writing this up (2026-09-05):

- **Naming / package homes** → the shared packages are `pyobs-js-core` and `pyobs-js-fits` (both
  verified free on npm), each in its own repo, published to npm; the mobile client repo is
  `pyobs-app`; the app's display name is "pyobs".

Still open / out of scope (for now):

- **Push notifications** — deferred, but scoped now because it shapes the event/state model:
  any socket dies on background/kill, so push is the only closed-app channel. Use cases:
  (a) critical alerts while nobody is watching (module ERROR transitions, bad weather with roof
  open, guiding lost, CRITICAL log events); (b) completion of long-running operations while the
  app is backgrounded. v1 ships without it. Costs when built: XEP-0357 server wiring (ejabberd
  supports the server side), an APNs/FCM relay, per-user opt-in and filtering (threshold-style
  rules need server-side or relay evaluation — no client code runs while the app is closed).
  Actionable now: keep ERROR states, weather events, and CRITICAL log levels distinguishable on
  the wire.
- **Desktop / client consolidation ("eventually replace pyobs-polaris")** — not decided. The
  UI-neutral core makes replacement with *some* desktop consumer feasible, but RN's desktop story
  is limited (react-native-windows/macos are out-of-tree, outside Expo; no native Linux target;
  Expo/EAS does no desktop builds). Realistic routes: desktop = `pyobs-web-client` (already
  mobile+desktop responsive), optionally wrapped in Tauri/Electron; react-native-windows/macos
  only for native feel; and a hard *native Linux desktop* requirement would reopen ADR 0018
  (Flutter is the one-codebase mobile + native-Linux option). Guardrail regardless of route:
  ADR 0017's core stays UI-framework-neutral. Feature parity with Polaris (FITS display, plots,
  runtime plugin widgets) is a separate product decision.
- **Bare RN vs Expo** if a future native module cannot be accommodated by Expo.

## References

- `specs/design/pyobs_2_0_wire_protocol.md` — the wire protocol, state, and access control this
  client implements.
- ADRs [0016](../adrs/0016-mobile-client-xmpp-over-websocket-not-direct-tcp.md),
  [0017](../adrs/0017-web-and-mobile-share-framework-agnostic-ts-core.md),
  [0018](../adrs/0018-mobile-app-framework-react-native-expo.md).
- pyobs/pyobs-core issue #884 — discussion thread and decision history.
- `pyobs-web-client`: `src/pyobs-codec.ts`, `src/composables/useXmpp.ts`, `packages/pyobs-fits`
  (extraction source for `pyobs-js-fits`), CLAUDE.md (mobile+desktop rule).
- ADR 0012 (explicit pubsub event subscription) and ADR 0002 (stream-conflict quit) in this
  repo.
