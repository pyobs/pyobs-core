# Plan: Surface unrecognized kwargs in `Object.__init__` instead of silently discarding them

Status: `comm_cfg` anchor leak fixed at the source (2026-08-17, PR pending); `environment`/`database`
question and `Object.__init__` enforcement (warn/raise) still open — see Decision

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

**Superseded 2026-08-17: fix the `comm_cfg` leak at its source instead of allowlisting it.**
Re-examined after `pyobs-core`'s own `pre_process_yaml` implementation
(`pyobs/utils/config.py:9-98`) turned out to make this tractable, not just a "clean fix in theory."
It isn't real YAML anchor/alias resolution — it's a bespoke text preprocessor: `{include file}` (no
key selector) splices the *whole* included file's parsed-and-redumped dict in at the marker
(`config.py:30`), and separately `reload_anchors()` regexes that same file's raw text for
`keyword: &anchor` pairs (`config.py:39,65-77`), which `replace_aliases()` then uses to textually
substitute every `<<: *anchor` elsewhere with a fresh dump of `dict_anchor[keyword]`
(`config.py:80-98`). So the anchor-holder key's name is already known by `pre_process_yaml` at the
exact point the leak happens — `reload_anchors()` returns `("comm_cfg", "comm")` directly.

**Fix:** in `pre_process_yaml`, for a whole-file `{include file}` (no key selector), drop `keyword`
from `include_dict` before it's dumped into `include` and spliced into `content`, for every
`keyword` that `reload_anchors(file)` reports. `comm_cfg` then never reaches the final config dict.
`<<: *comm` still resolves correctly, since `replace_aliases` reads the anchor's value from the
original included file, not from the (now-trimmed) spliced copy. Only apply the drop when the
include has no key selector — a file that deliberately does `{include comm.shared.yaml comm_cfg}`
to grab the anchor-holder's value directly must keep it; `include_parts()` already distinguishes
this case (`config.py:47-62`). Add a regression test for both: whole-file include drops the
anchor-holder key, key-selected include of the same key does not.

This is a ~5-line change to one function in the include mechanism itself, not a new YAML loader —
low enough risk to do directly rather than staging behind a warn+allowlist step in `Object.__init__`.

**Implemented 2026-08-17.** One non-obvious wrinkle found while implementing: `comm.shared.yaml`'s
*only* top-level key is `comm_cfg` (the anchor holder), so a whole-file include of it filters down to
an **empty** `include_dict`. `yaml.dump({})` produces `"{}\n"`, a flow-style node — spliced into a
document that continues as a block-style mapping below it (`comm:\n  <<: *comm\n  ...`), that isn't
valid YAML (`ParserError: expected '<document start>', but found '<block mapping start>'`). Fixed by
emitting an empty string instead of `"{}\n"` when the filtered `include_dict` is empty, so the
placeholder is dropped entirely rather than replaced with an empty mapping. Verified end-to-end
against a real fleet config (`pyobs-monet/config/central/imagedb.yaml`): `comm_cfg` no longer appears
in the parsed result, `comm.class`/`comm.domain`/`comm.user` still resolve correctly via the alias.

**`environment`/`database` (monet central configs) are a separate, still-open problem, not fixed by
the above.** They aren't an anchor-holder pattern at all (no `&anchor` — see the open-question note
below dated 2026-08-17): they're just top-level keys from a whole-file splice that nothing appears
to consume, in configs whose own `class: pyobs.Application` key doesn't match how
`Application.__init__` loads a config file. Until that's resolved, don't allowlist or assume they're
dead weight.

**Enforcement level at `Object.__init__` once `comm_cfg` is fixed at the source:** re-evaluate warn
vs. raise then. With the anchor leak gone, the main known source of "legitimate but unconsumed"
kwargs disappears — but `environment`/`database` staying unresolved means a hard `raise` fleet-wide
(monet in particular) is still not safe to flip on until that question is closed.

## Open questions

- Is `environment:`/`database:` in monet central configs actually dead weight, or do those configs
  build the `Environment`/`Database` objects some other way? (Investigation above found no consumer;
  confirm before relying on the allowlist/warn decision.)
  - **2026-08-17 partial check, inconclusive:** several `pyobs-monet/config/central/*.yaml` files
    that include `environment.shared.yaml`/`database.shared.yaml` (e.g. `imagedb.yaml`,
    `joomla-proxy.yaml`) carry a top-level `class: pyobs.Application` key, which doesn't match how
    `Application.__init__` (`pyobs-core/pyobs/application.py:230-263`) actually loads a config: it
    reads `cfg["class"]` to pick the module class, then calls `get_object(cfg, Module)` on the
    *whole* dict — so `cfg["class"]` would need to name a `Module` subclass, not `pyobs.Application`
    itself, or `create_object` would try to build an `Application` and fail the `isinstance(obj,
    Module)` check. Either these specific central configs are stale/unused (plausible — the fleet
    has moved to `pyobs.Application` invoked as `pyobs <configfile>` from the CLI, not embedded as a
    YAML key) or there's a second load path not found yet. Needs resolving before trusting the
    dead-weight conclusion — don't allowlist `environment`/`database` off this evidence alone.
- `comm_cfg` is the only anchor-holder key found across the fleet. Confirm no other shared file uses
  the same `key: &anchor` pattern (e.g. future `database.shared`/`environment.shared` variations) so
  the allowlist isn't silently incomplete.

## Implementation checklist

- [x] Investigate: enumerate classes that pass unconsumed kwargs up to `Object.__init__` in
      practice, and check whether any real YAML configs in this repo or known deployments rely on
      extra ignored keys (done — see findings above: 126 subclasses, `comm_cfg` anchor leak is real
      and documented)
- [x] Decide raise vs. warn (superseded 2026-08-17 — see Decision: fix the `comm_cfg` leak at its
      source instead of allowlisting it in `Object.__init__`)
- [x] Fix the `comm_cfg` anchor-holder leak at its source in `pre_process_yaml`
      (`pyobs/utils/config.py`): whole-file includes (no key selector) now drop any key
      `reload_anchors()` identifies as an anchor holder for that file before splicing, and an
      empty resulting splice is dropped entirely rather than emitting `"{}\n"`. Regression tests
      added in `tests/utils/test_config.py`; verified against a real `pyobs-monet` config.
- [ ] `environment`/`database` (monet central configs) still unresolved — see the 2026-08-17
      open-question note above; not fixed by the `comm_cfg` change and not safe to allowlist yet.
- [ ] Decide and implement warn vs. raise for any remaining leftover kwargs at `Object.__init__`,
      once the `environment`/`database` question is closed.
- [ ] Update this doc's `Status:` to fully `implemented, closed` once the above lands.
