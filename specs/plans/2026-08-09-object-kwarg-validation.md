# Plan: Surface unrecognized kwargs in `Object.__init__` instead of silently discarding them

Status: `comm_cfg` anchor leak fixed at the source, merged 2026-08-17 (PR #773, squash-merged as
`a5646fb8`); `environment`/`database` confirmed gone 2026-08-18 (no longer a blocker); a full
fleet-wide cleanup pass (2026-08-18) fixed every other confirmed dead/misplaced/typo'd kwarg found
by re-running the investigation as a static check across `pyobs-monet`/`pyobs-iagvt`/`pyobs-iag50`/
`pyobs-polaris` — see the new section below. `Object.__init__` warn/raise enforcement is the one
remaining undecided item, and nothing found is blocking it anymore.

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

**PR review (github.com/pyobs/pyobs-core/pull/773, thusser) found two silent-data-loss bugs in the
first pass, both fixed before merge:**

1. The empty-splice-drop above wasn't scoped to whole-file includes, so a *keyed* include that
   legitimately selects an empty mapping (`{include file key}` where `key`'s value is `{}`) was
   also silently turned into `null` instead of staying `{}`. Fixed by gating that branch on the
   same `not key.strip()` (whole-file) condition as the anchor-drop itself.
2. Anchor-holder detection reused `reload_anchors()`, whose regex matches `keyword: &anchor` at
   *any* nesting depth, not just top-level. A top-level key could be wrongly dropped from a
   whole-file include just because an unrelated *nested* key elsewhere in the same file happened to
   share its name and carry an anchor. Fixed by adding `top_level_anchor_keywords()` — a
   line-anchored (`^`, no leading whitespace) regex restricted to unindented keys — used only for
   the drop decision; `reload_anchors()` itself is unchanged, since `replace_aliases()` still needs
   to resolve anchors at any nesting depth.

Both reproduced from the reviewer's examples before fixing, to confirm they were real; regression
test added for each. Re-verified against all 803 YAML files across `pyobs-monet`, `pyobs-iagvt`, and
`pyobs-iag50`: no `comm_cfg` leaks in any consuming config; the two files that still error
(`pyobs-monet/config/south/monet/_update_imagedb.yaml`'s missing `database.shared.yaml`, and
`pyobs-iag50/config/iag50cam/telescope.yaml`'s malformed `include _comm.yaml}` missing its opening
brace) are pre-existing fleet-config bugs, unrelated to this change and unaffected by it either way.

**`environment`/`database` (monet central configs) — resolved 2026-08-18: confirmed gone, no longer
a blocker.** Consistent with the `class: pyobs.Application` mismatch noted below: the containing
`pyobs-monet/config/central/*.yaml` files turned out to be pre-2.0-migration dead files entirely
(confirmed independently while static-checking the fleet — every class they reference,
`pyobs.Application`, `pyobs.auth.*`, `pyobs.database.Database`, `pyobs.modules.environment.Environment`,
`pyobs.modules.imagedb.ImageDB`, `pyobs.modules.pipeline.Pipeline`, `pyobs.modules.proxy.HTTP2XMPP`,
fails to import against current pyobs-core). Not touched (out of scope, being replaced rather than
fixed), but no longer something a `raise` decision needs to account for.

## Fleet-wide cleanup pass (2026-08-18)

With `comm_cfg` fixed and `environment`/`database` resolved, re-ran the investigation as a static
check to see what *else* `Object.__init__`'s `**kwargs` is silently swallowing fleet-wide, before
deciding warn vs. raise. Method: for every class referenced anywhere in a config (recursively, any
nesting depth), union every parameter name declared across its full `__init__` MRO chain, and flag
any config key not in that union. Chose this over actually constructing every module (which the
original plan's checklist implied) specifically to avoid running real driver `__init__` code against
live telescope hardware/IPs (e.g. `BrotRaDecTelescope`'s configured `host:`) — `Object.__init__`
separates construction from `open()`/connect by convention, but that can't be assumed for every
third-party driver. Installed all 9 local sibling driver packages
(`pyobs-monet`/`-iagvt`/`-brot`/`-iag50`/`-aravis`/`-asi`/`-sbig`/`-gemini`/`-fli`) editable, no-deps,
to resolve classes for the check. Covered 815 real config files across `pyobs-monet`, `pyobs-iagvt`,
`pyobs-iag50`, and `pyobs-polaris` (833 found, minus 2 pre-existing unrelated errors, minus 2 CMake
build-log YAMLs the file glob picked up by accident).

**Every genuinely dead/misplaced/typo'd key found was fixed, one at a time, each verified against
source before touching config:**

- `name:` (8 sites, `pyobs-polaris/fixtures/*.yaml` ×7, `pyobs-iag50/config/*/sbig6303e.yaml` ×2) —
  confirmed dead by design: `Module.name` is a computed property reading `self.comm.name`
  (`pyobs/modules/module.py:419`,`:154`), never a config key. Removed.
  (`pyobs-polaris` `2cebf5d`, `pyobs-iag50` `0e9b518`)
- `ImageWriter.root` (2 sites) — no such param, nothing pops it from kwargs. Removed.
  (`pyobs-monet` `3441603`)
- `AutoGuiding.guider:` nested object (2 sites) — superseded by the required `pipeline:` list
  (`BasePointing.__init__`, `pyobs/modules/pointing/_base.py:23-27`, docstring: "MUST include a step
  calculating offsets!"); both sites already had a correct `pipeline:` ending in a real offset step.
  Removed. (`pyobs-monet` `bd11b37`)
- `HttpFileCache.hostname` (5 sites across `pyobs-monet`/`pyobs-iagvt`/`pyobs-iag50`) — no such
  param, no host-related code anywhere in the class. Removed.
  (`pyobs-monet` `47e433f`, `pyobs-iagvt` `586fd11`, `pyobs-iag50` `c2209b6`)
- `new_images_channel:` (7 sites, `pyobs-monet`) — grepped all of `pyobs-fli`, `pyobs-sbig`, and
  `pyobs-monet`'s own driver code: zero references anywhere. Removed. (`pyobs-monet` `f978069`)
- `HttpFile` `username:`/`password:` (1 site) — security-relevant: `HttpFile` only supports
  token-based bearer auth, not Basic Auth; these looked like real credentials for a remote HTTPS
  endpoint, silently never sent. Removed (confirmed with user the endpoint doesn't need them).
  (`pyobs-monet` `1f7d121`)
- `max_offsets` → `max_offset` typo (3 sites, `pyobs-monet`) — real param is singular
  (`ApplyAltAzOffsets.__init__`); all three modules had been running with the class default (30
  arcsec) instead of the configured 3600/3600/2. **Behavior fix, not just cleanup** — renamed to the
  correct key so the intended values take effect; affected modules need a restart to pick it up.
  (`pyobs-monet` `4c07a45`)
- `twilight:` misplaced (1 site, `pyobs-iag50`) — real param is `AstroplanScheduler.twilight`
  (nested `scheduler:` block), but sat one level too shallow, alongside the outer `Scheduler` class;
  silently dropped there, so the module ran with the `"astronomical"` default instead of the
  configured `"nautical"`. **Behavior fix** — moved to where it's read.
  `LcoObservationArchive`'s `instrument:`/`instrument_type:` (same file) — docstring documents
  `instrument` as a real param, but it's never declared or used anywhere in the class; confirmed
  dead, removed alongside. (`pyobs-iag50` `13e1846`)
- `FlatFielder.combine_binnings` (2 sites, `pyobs-iag50`) — one silently dropped (plain `Object`
  subclass, confirmed dead); the other, under `SkyFlatsScript` (a pydantic model, `extra="forbid"`
  since PR #762), was **actively failing pydantic validation** (`ValidationError: Extra inputs are
  not permitted`) — `Mastermind` could not start with that config as it stood. Exactly the failure
  mode this whole plan wants: loud, not silent. Removed both. (`pyobs-iag50` `797dcd9`)

**One false positive caught before editing anything:** `pyobs_iagvt.modules.FiberCamera`'s
`rotation_correction_coefficients` looked dead by signature inspection, but is actually consumed via
a manual `kwargs` dict pop in the constructor body (`fibercamera.py:34-37`), not a named parameter —
the static check's blind spot. Left untouched. Same caution applies to anything not yet
individually verified below.

**Explicitly not investigated/fixed, by choice, not oversight:**
- `pyobs-monet/config/north/monet/robotic.yaml`'s `LcoTaskArchive`/`scripts:` findings (missing
  required `instrument_type`, dead top-level `site`/`telescope`/`filters`/`camera`/`roof`/
  `autoguider`, unclear `scripts:` dispatch wiring) — this specific config is being replaced by the
  robotic backend (like `south/monet` already uses), not fixed, per explicit direction.
- `pyobs_iag50.Pointing`'s 4 leftover keys — `pyobs-iag50` is pinned to `pyobs-core<2` (confirmed via
  a real dependency-resolution conflict installing it), so its own code doesn't even import cleanly
  against current pyobs-core; not reliable to evaluate until it's ported.
- The ~45 classes whose imports failed during the static check (mostly missing third-party hardware
  SDKs — `pybrotlib`, `zwoasi`, `serial`, `aioserial`, `pyftscontrol`, `matplotlib` — expected and
  can't be tested off-hardware) remain unverified either way, not confirmed safe.

## Open questions

- ~~Is `environment:`/`database:` in monet central configs actually dead weight?~~ **Resolved
  2026-08-18: confirmed gone** — see Decision. The containing `pyobs-monet/config/central/*.yaml`
  files are pre-2.0-migration dead files (every class they reference fails to import against current
  pyobs-core), not touched (being replaced, not fixed), no longer a factor in the warn/raise call.
- ~~Is `comm_cfg` the only anchor-holder key across the fleet?~~ **Resolved** — the 2026-08-18
  fleet-wide static check covered all 815 real config files across `pyobs-monet`/`pyobs-iagvt`/
  `pyobs-iag50`/`pyobs-polaris` and found zero other `*_cfg`-style anchor-holder leaks anywhere.
- **New, 2026-08-18:** should `Object.__init__` warn or raise once implemented? Nothing found in the
  fleet cleanup pass argues for `warn`-as-a-permanent-state anymore — every real leftover-kwarg
  pattern found (dead keys, misplaced keys, a real typo) was fixable outright, not something that
  needs a grace period. The only remaining unknowns are the ~45 classes that couldn't be
  import-checked (see above) and any deployment outside this workspace's four local fleets (there may
  be others not checked here). Still an open call, not yet made.

## Implementation checklist

- [x] Investigate: enumerate classes that pass unconsumed kwargs up to `Object.__init__` in
      practice, and check whether any real YAML configs in this repo or known deployments rely on
      extra ignored keys (done — see findings above: 126 subclasses, `comm_cfg` anchor leak is real
      and documented)
- [x] Decide raise vs. warn (superseded 2026-08-17 — see Decision: fix the `comm_cfg` leak at its
      source instead of allowlisting it in `Object.__init__`)
- [x] Fix the `comm_cfg` anchor-holder leak at its source in `pre_process_yaml`
      (`pyobs/utils/config.py`): whole-file includes (no key selector) now drop any top-level key
      that carries an anchor, and an empty resulting splice is dropped entirely rather than
      emitting `"{}\n"`. Regression tests added in `tests/utils/test_config.py`; verified against a
      real `pyobs-monet` config and, in review, against all 803 fleet configs across `pyobs-monet`/
      `pyobs-iagvt`/`pyobs-iag50`. Merged 2026-08-17: PR #773, squash-merged as `a5646fb8`.
- [x] `environment`/`database` (monet central configs) — resolved 2026-08-18: confirmed gone, no
      longer a blocker.
- [x] Fleet-wide cleanup pass (2026-08-18): re-ran the investigation as a static check across all
      four local fleets (815 real config files) and fixed every confirmed dead/misplaced/typo'd
      kwarg found — see the new section above for the full list and commit references.
- [ ] Decide and implement warn vs. raise for any remaining leftover kwargs at `Object.__init__`.
      Nothing found is blocking this anymore — the only remaining item.
- [ ] Update this doc's `Status:` to fully `implemented, closed` once the above lands.
