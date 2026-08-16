# Plan: Surface unrecognized kwargs in `Object.__init__` instead of silently discarding them

Status: investigated — findings and decision recorded 2026-08-15; implementation not started

Related: `specs/plans/night-archive-io-hardening.md` — where this was first flagged (a typo in a
`Reduction`/`Night` YAML config silently does nothing instead of raising). That plan fixes the
local, trivial case (`Reduction` doesn't inherit from `Object`, so its own `**kwargs: Any` is just
removed). This plan is the systemic version, for the classes that actually need `**kwargs` to
thread framework parameters through subclass chains.

## Problem

`pyobs.object.Object.__init__` (`pyobs/object.py:242`) is the base class nearly every config-driven
object in pyobs-core eventually inherits from. It explicitly consumes `vfs`, `comm`, `timezone`,
`location`, `observer`, and ends with `**kwargs: Any` that silently drops anything left over — no
warning, no error. Since `pyobs.object.create_object` builds objects straight from YAML config dicts
(`klass(*args, **cfg, **kwargs)`), a misspelled config key anywhere in that chain (e.g.
`instrment` instead of `instrument` on some module, or a typo'd option meant for a subclass several
levels down) is silently absorbed at `Object.__init__` and never surfaces as an error — the object
just gets built without that setting, and nothing tells you why your config didn't do what you
expected.

This came up designing pipeline-web's pipeline builder: an operator typing raw JSON into a step's
config field gets no feedback on a typo — it just silently doesn't apply.

## Why not fixed already / why it's not trivial

Unlike `Reduction`, most `Object`-derived classes *need* the passthrough — subclasses don't
redeclare every parent parameter, they rely on `**kwargs` flowing up through `super().__init__(**kwargs)`
calls until something consumes each key. A validation added at `Object.__init__` needs to only catch
keys that *nothing* in the chain consumed, not raise on every subclass's legitimate omission of
some parent's kwarg.

The other real risk: pyobs-core configs may have existing, working setups that rely on the current
silence — e.g. a shared YAML block reused across multiple object types where not every key applies
to every one of them. A hard `raise` here could break real deployments that currently work by
accident. This needs checking against real configs before deciding enforcement level (raise vs. warn).

## Non-goals (for now — this is a stub, scope may change once investigated)

- Changing `Reduction`'s `**kwargs` — handled directly in `night-archive-io-hardening.md`, since
  that's a local dead-end case, not this systemic one.
- Any change to `create_object`/`get_object` themselves — the likely fix point is `Object.__init__`
  specifically, not the object-construction helpers, but that's to be confirmed once investigated.

## Investigation findings (2026-08-15)

**Scale.** 126 classes in pyobs-core (transitively) inherit from `Object`; essentially all of them
end `__init__` with `**kwargs` and pass it up via `super().__init__(**kwargs)`/`Object.__init__(self,
**kwargs)` to thread the framework params (`vfs`/`comm`/`timezone`/`location`/`observer`) through
multi-level subclass chains. So the passthrough is ubiquitous, not exceptional.

**Real configs do rely on silent ignoring — this is the decisive finding.** The YAML include/anchor
mechanism leaks keys that are never meant to be consumed by the object. Concretely, every fleet's
`comm.shared.yaml` (or `_comm.yaml`) defines `comm_cfg: &comm` as a YAML-anchor holder:

```yaml
comm_cfg: &comm
  class: pyobs.comm.xmpp.XmppComm
  domain: example.com
```

`{include comm.shared.yaml}` (no key selector) splices the whole file into the module config, so
`comm_cfg` becomes a top-level key in the config dict. `comm: <<: *comm` uses the anchor, but
`comm_cfg` itself survives into the dict and is passed to the object constructor, where it lands in
`Object.__init__`'s `**kwargs` and is silently dropped. This is not accidental: it's documented as
*the* supported pattern in the `XmppComm` docstring (`pyobs/comm/xmpp/xmppcomm.py:114-131`) and
appears in every config across monti, monet, iagvt, and polaris.

Verified concretely: preprocessing `pyobs-monti/config/_pointing.yaml` yields `comm_cfg` as a
top-level key, and building a `Module` subclass with `comm_cfg=...` succeeds silently.

A second, smaller leak: monet central configs include `environment.shared.yaml` and
`database.shared.yaml`, which wrap their content under top-level `environment:`/`database:` keys that
also survive into the config dict and are dropped (nothing in `Application`/`Module` consumes them).

**Consequence for raise vs. warn.** A hard `raise` at `Object.__init__` for leftover kwargs would
break every fleet config, because `comm_cfg` (and the monet `environment`/`database` wrappers) are
legitimate-but-unconsumed keys produced by the include mechanism, not typos. `raise` is off the table
unless the leak is fixed at its source first.

## Decision

**Enforcement level: warn, not raise, for now.** The leftover-kwargs check at `Object.__init__` should
`log.warning` the unrecognized keys rather than raise. Rationale: the config include/anchor mechanism
currently leaks `comm_cfg` (documented) and, on monet, `environment`/`database` wrappers into every
config; raising would break those deployments.

**The real fix is upstream of `Object.__init__`, not at it.** Two candidate places to stop the leak
so `warn` can later become `raise` without breakage:

1. `pre_process_yaml` / the include mechanism: strip a key that was introduced purely as an anchor
   holder (a key whose only role is `key: &anchor` and whose value is consumed via `<<: *anchor`
   elsewhere). Needs a heuristic — e.g. drop any top-level key that is never referenced as `*anchor`
   and is a dict — or an explicit convention (e.g. keys named `*_cfg` are include-internal). This is
   the clean fix but touches the config loader everyone depends on, so it needs care.
2. `Object.__init__` (or `get_object`): warn on leftover kwargs, and treat `comm_cfg` (and any
   future documented anchor-holder keys) as a known ignorable, so the warning is reserved for
   genuinely unknown keys.

The two are complementary: (2) ships now as a cheap warning with a small allowlist; (1) removes the
allowlist entries at the source later, at which point (2)'s warning can be promoted to a `raise`.

## Open questions

- Is `environment:`/`database:` in monet central configs actually dead weight, or do those configs
  build the `Environment`/`Database` objects some other way? (Investigation above found no consumer;
  confirm before relying on the allowlist/warn decision.)
- `comm_cfg` is the only anchor-holder key found across the fleet. Confirm no other shared file uses
  the same `key: &anchor` pattern (e.g. future `database.shared`/`environment.shared` variations) so
  the allowlist isn't silently incomplete.

## Implementation checklist

- [x] Investigate: enumerate classes that pass unconsumed kwargs up to `Object.__init__` in
      practice, and check whether any real YAML configs in this repo or known deployments rely on
      extra ignored keys (done — see findings above: 126 subclasses, `comm_cfg` anchor leak is real
      and documented)
- [x] Decide raise vs. warn (see Decision: warn now, raise later after fixing the include leak)
- [ ] Implement the warn check in `Object.__init__` (allowlisting `comm_cfg` and the monet
      `environment`/`database` wrappers, or better, fixing the include mechanism to strip them)
- [ ] Tests: a class with a typo'd kwarg warns; a class using legitimate multi-level `**kwargs`
      passthrough still works; `comm_cfg` does not warn
- [ ] Update this doc's `Status:` to `implemented` once landed
