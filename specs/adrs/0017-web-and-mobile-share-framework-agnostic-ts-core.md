# `pyobs-web-client` and the mobile app share one framework-agnostic TypeScript core

status: accepted
date: 2026-09-05

Repos: pyobs-core, pyobs-web-client, pyobs-js-core (new repo + npm package, planned), pyobs-app (planned)

## Context and Problem Statement

pyobs's non-Python clients each re-implement the wire protocol. `pyobs-web-client` (Vue 3) holds
its protocol logic in `src/pyobs-codec.ts` (the `urn:pyobs:rpc:1` value/XML codec plus disco#info
schema parsing) and `src/composables/useXmpp.ts` (connection lifecycle, presence/disco discovery,
RPC, pubsub state/event subscriptions, reconnect), on top of strophe.js. The planned mobile app
(ADR 0018: React Native) shares TypeScript with the web client but would otherwise re-implement
that whole layer a second time. Two implementations of a versioned wire protocol drift and double
the test surface — the opposite of the pyobs 2.0 direction of making the wire protocol explicit
(`specs/design/pyobs_2_0_wire_protocol.md`).

## Considered Options

* **Each app keeps its own protocol implementation** (status quo plus a second one inside the
  app) — two codecs, two discovery/RPC/pubsub stacks, each tracking interface versioning and
  wire-format changes separately (rejected: guaranteed drift).
* **Extract a framework-agnostic TypeScript core package consumed by both apps** (chosen): pure
  protocol logic with no Vue, no React Native, no browser DOM; thin per-UI adapters (Vue
  composable; RN hook/provider).
* **A non-TypeScript shared core** (e.g. Rust/WASM) — breaks the direct code sharing with
  `pyobs-web-client`'s TS stack and adds toolchain weight without a payoff here.

## Decision Outcome

Extract the web client's protocol layer into one framework-agnostic TypeScript package —
`pyobs-js-core`, in its own repo, published to npm — consumed by both `pyobs-web-client` and the
mobile app (`pyobs-app`). The core stays UI-framework-neutral (events or a plain
store), is DOM-free, and no React Native (or Vue) types may leak into it — so any future desktop
client can sit on the same core. Its FITS sibling (`pyobs-js-fits`) follows the same shape (own
repo, published to npm, extracted from the web-client workspace) — see the design doc.

## Why

- TypeScript is shared by the Vue web app and the React Native app (ADR 0018) — the framework
  pairing that allows this without a port.
- The web client's existing unit/e2e suites become the regression net for the core before any
  mobile code exists (design doc, Phasing).
- Protocol behavior (interface versioning, RPC encoding, pubsub semantics) changes once and ships
  to every client in lockstep.

## Consequences

- Refactor of `pyobs-web-client` to remove three browser couplings: (1) `src/pyobs-codec.ts`
  builds XML via the browser DOM (`document.implementation.createDocument`,
  `document.createElement`) for strophe.js — must move to a platform-neutral XML layer
  (`@xmpp/xml`/ltx or the stanza.js family); (2) strophe.js itself is browser-first — swap to an
  RN-capable XMPP core with a WebSocket transport (`@xmpp/client` or stanza.js; verify in a spike
  on both targets); (3) `src/composables/useXmpp.ts` mixes Vue state (`ref`s, `sessionStorage`,
  `window.location`) with protocol logic — split into core plus a thin Vue adapter.
- Expo/React Native inside a workspace monorepo needs Metro configuration
  (`watchFolders`/`nodeModulesPaths`) for the shared package.
- FITS rendering stays web-only (canvas has no RN equivalent); only the HTTP/token fetching
  logic is shared (design doc).
