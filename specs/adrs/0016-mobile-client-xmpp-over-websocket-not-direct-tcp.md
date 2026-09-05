# Mobile client speaks XMPP over WebSocket (RFC 7395), not direct TCP

status: accepted
date: 2026-09-05

Repos: pyobs-core, pyobs-web-client, pyobs-app (planned)

## Context and Problem Statement

The planned smartphone/tablet client for pyobs (issue #884; design
`specs/design/mobile-app-and-shared-ts-client-core.md`) must connect to the same XMPP-based
control plane as the existing clients. Those already split transports: `pyobs-core`/`pyobs-gui`
and `pyobs-polaris` use direct TCP c2s (port 5222 with STARTTLS; slixmpp resp. QXmpp), while
`pyobs-web-client` uses XMPP over WebSocket (RFC 7395) against ejabberd's `mod_websockets`
(`ws(s)://<domain>:5280/ws`). All meet at the same ejabberd, which routes TCP and WebSocket
sessions interchangeably, so every wire feature above the transport (presence, disco#info,
XEP-0009 RPC, XEP-0060 pubsub, XEP-0199 keepalive) is identical over either pipe. The question is
only which transport the new mobile client should use — not whether it speaks XMPP at all (the
non-XMPP alternative was settled at the pyobs 2.0 level: `specs/design/pyobs_2_0_wire_protocol.md`).

## Considered Options

* **Direct XMPP over TCP (c2s, port 5222/STARTTLS)** — as used by `pyobs-core` (slixmpp) and
  `pyobs-polaris` (QXmpp). Mature on desktop, where the client library owns the socket stack.
  On cross-platform mobile frameworks the picture is different: solid XMPP-over-TCP libraries
  are thin, and the realistic options are native per-platform stacks (Smack on Android,
  XMPPFramework on iOS — two codebases or a wrapper plugin) or early-stage wrappers (e.g.
  Flutter's `fxmpp`).
* **XMPP over WebSocket (RFC 7395)** — as used by `pyobs-web-client` against the existing
  ejabberd `/ws` endpoint (chosen).
* **Non-XMPP control channel** (REST or a bespoke WebSocket protocol) — rejected at the pyobs 2.0
  level already; XMPP as transport (addressing, auth, discovery, pubsub) is a settled pillar.

## Decision Outcome

The mobile client uses **XMPP over WebSocket (RFC 7395)** to the existing ejabberd WebSocket
endpoint (`wss://…:5280/ws`, or port 443 when proxied) — the same transport as
`pyobs-web-client`. Direct TCP remains the right choice only where the client library is
TCP-native and proven on the target platform (the Qt/QXmpp route to mobile, or a native dual
stack); this ADR does not change those clients.

## Why

- **Mobile library reality is the deciding factor.** WebSocket is first-class in every
  cross-platform mobile runtime (React Native built-in `WebSocket`, Flutter
  `web_socket_channel`/`dart:io`, Qt `QWebSocket`), so the app implements a thin RFC 7395 stanza
  layer on a maintained transport instead of inheriting two native XMPP stacks' quirks or an
  alpha wrapper.
- **Zero server-side work.** ejabberd already serves `/ws` on port 5280 — `pyobs-web-client`
  logs in through it. The mobile client adds a consumer, not new infrastructure.
- **Network friendliness.** `wss://` on 443 passes carrier NATs, captive portals and corporate
  proxies that routinely block arbitrary 5222; TLS is part of the ws layer and validated against
  the platform trust store, avoiding in-app STARTTLS plumbing.
- **Backgrounding is not a TCP advantage.** iOS suspends any socket when the app backgrounds;
  Android Doze kills connections. Reconnect-on-foreground plus push (XEP-0357 → APNs/FCM) is
  required regardless of transport.

## Consequences

- The XMPP core chosen for the app must support a WebSocket transport and must not assume a
  browser DOM (see ADR 0017).
- The pyobs wire semantics stay unchanged; interop with the TCP-speaking modules and clients is
  via ejabberd, which already routes both transports.
- `pyobs-core` itself needs no runtime change for this decision; it only documents the new
  client family.
