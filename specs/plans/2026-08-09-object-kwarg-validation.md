# Plan: Surface unrecognized kwargs in `Object.__init__` instead of silently discarding them

Status: draft (stub — not yet investigated in depth)

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

## Open questions (this plan needs an investigation pass before it has a Decision section)

- How many classes in pyobs-core actually reach `Object.__init__` via `super().__init__(**kwargs)`,
  and does any of them intentionally rely on extra unconsumed kwargs being silently ignored (e.g.
  shared config blocks)? Needs a real search, not a guess.
- Raise (`TypeError`) vs. `log.warning(...)` for leftover kwargs at `Object.__init__`? Raising is
  more useful (fails fast, matches what removing `Reduction`'s `**kwargs` does) but riskier against
  existing configs; warning is safer to ship first and tighten later once confirmed nothing depends
  on the silence.
- Should this be opt-in per class (e.g. a class-level flag) rather than global, given the risk of
  breaking configs that happen to rely on today's silence?

## Implementation checklist

- [ ] Investigate: enumerate classes that pass unconsumed kwargs up to `Object.__init__` in
      practice, and check whether any real YAML configs in this repo or known deployments rely on
      extra ignored keys
- [ ] Decide raise vs. warn (see Open Questions)
- [ ] Implement the check in `Object.__init__`
- [ ] Tests: a class with a typo'd kwarg surfaces the problem; a class using legitimate
      multi-level `**kwargs` passthrough still works
- [ ] Write this plan's Decision section properly once the investigation above is done — this
      stub intentionally skips straight to Open Questions since the shape of the fix isn't decided
- [ ] Update this doc's `Status:` to `implemented` once landed
