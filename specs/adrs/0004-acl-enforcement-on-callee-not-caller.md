# Enforce access control on the callee, not the caller

status: accepted
date: 2026-07-10

## Context and Problem Statement

Before Access Control (ACLs), pyobs assumed a closed, mutually-trusting fleet: any
authenticated client could call any method on any other client that exposes it. That stops
being fine once a fleet has multiple operators/scripts with different privilege levels — e.g.
a GUI operator who should be able to move a telescope but not reset camera firmware, or a
scheduler that should only ever call `expose`/`abort` on a camera, never its cooling controls.
Identity already flows through `Module.execute(method, *args, **kwargs)` on every backend via a
`sender` kwarg (the caller's JID local part for XMPP, the caller's own name for `LocalComm`),
so the question was where to put the actual authorization check, not how to identify the caller.

## Considered Options

* Enforce on the caller: give each module a "who am I allowed to talk to" allowlist that it
  consults before making an outgoing call
* Enforce on the callee: give each module a policy describing who may call it, checked inside
  `Module.execute()` before dispatching an incoming call

## Decision Outcome

Chosen option: enforce on the callee. A caller-side allowlist is just the caller's own code —
a bug, a misconfiguration, or a compromised process routes around it trivially, since nothing
external ever validates that the caller actually consulted it. The module being called is the
only party that can make the check stick, so policy is declared on, and enforced by, the
target: an optional `acl:` config block (sibling of the existing `comm:` block) specifying
either `allow` (least-privilege allowlist, method-level) or `deny` (coarse quarantine,
whole-caller), checked inside `Module.execute()` immediately before dispatch. No `acl:` block
at all means fully open — additive and backward-compatible, the same migration shape as
`Interface.version` defaulting to `1`. See `specs/design/pyobs_2_0_wire_protocol.md`'s Access
Control section for the full `allow`/`deny`/`mode` design built on top of this decision.

### Consequences

* Good, because the check is authoritative regardless of caller behavior — a caller cannot
  bypass it by skipping its own-side logic, correctly or maliciously
* Good, because it composes with a single enforcement point (`Module.execute()`) shared by
  every `Comm` backend, rather than needing to be duplicated per-backend or per-caller
* Good, because a module's full reachability policy is legible from its own config file — no
  need to audit every potential caller's code to know who can reach a sensitive module
* Neutral, because callee-side enforcement depends on transport-level authentication (XMPP
  SASL login) already vouching for the JID a `sender` string is derived from — this decision is
  authorization only, layered on existing authentication, not a replacement for it
* Bad, because a caller gets no proactive signal that a call will be denied before making it
  (addressed separately by `IModule.get_permitted_methods()`, not by this decision)
