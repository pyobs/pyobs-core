# `IConfig` stays a stringly-keyed name/value fallback, not a typed interface

status: accepted
date: 2026-07-21

## Context and Problem Statement

`IConfig` (`pyobs/interfaces/IConfig.py`) exposes config as `get_config_value(name: str) ->
ConfigValue` / `set_config_value(name: str, value: ConfigValue)` — a stringly-keyed bag with no
per-field semantics in the method signature itself. Every other interface in the 2.0 line does
the opposite: behavior is encoded in the signature (`set_gain(gain: float)`,
`ICooling.set_cooling(...)`), so a caller and a type checker both know exactly what's being set
without consulting a runtime name string. Read next to that convention, `IConfig`'s weak typing
looks like an oversight — something to "fix" by giving it typed accessors, or by folding it into
whatever composite interface a module already implements.

The question is whether that reading is correct: should `IConfig` be tightened up, or does its
genericness serve a purpose that a typed signature structurally can't?

## Considered Options

* Tighten `IConfig` itself — add typed get/set methods, or otherwise make it carry per-field
  semantics like the rest of the 2.0 interfaces
* Keep `IConfig` exactly as generic as it is today, and treat "this config value's type/behavior
  matters" as the signal to move it *off* `IConfig` and onto (a) a dedicated typed interface
  method, or (b) `IStructuredConfig` (see `specs/design/istructuredconfig.md`) for values that
  are really one structured object, not independent scalars

## Decision Outcome

Chosen option: keep `IConfig` generic, and treat it as the deliberate fallback for config values
that haven't "graduated" into their own typed interface — not a defect to be fixed. `IConfig`
exists precisely for settings a module wants to expose adjustably that don't (yet, or ever)
warrant a dedicated method: there is no way to make `get_config_value`/`set_config_value` more
specific without it stopping being `IConfig` and becoming a new, narrower interface instead. The
genericness is the feature — it's what lets `IConfig` cover arbitrary, module-specific knobs
without every module author inventing a new interface for each one.

This decision doesn't resolve where any *given* value should live — it establishes the decision
framework for that instead, exercised repeatedly against concrete cases:

* **Stays on `IConfig`** when a value is an independent scalar with no behavior beyond
  get/set — e.g. several unrelated numeric knobs on a camera module, each tunable on its own,
  none of which changes what any method signature means.
* **Moves to a dedicated typed interface** when a value's type is actually meaningful to
  callers — e.g. a mode-like field that should be constrained to an enum of valid options and
  read/written through its own method (`IMode.set_mode(mode: ...)`), not a bare string that
  happens to be validated at runtime.
* **Becomes a structured object via `IStructuredConfig`** when several values are not
  independent — they're fields of one config object applied atomically, where get/set-per-field
  would let a caller observe or apply a half-updated, inconsistent state.

### Consequences

* Good, because `IConfig` keeps working as a low-ceremony fallback — a module author isn't
  forced to design and register a new interface just to expose one adjustable scalar
* Good, because the graduation path is legible: a value's own requirements (does its type
  matter to callers? do several values need to move atomically?) determine when it leaves
  `IConfig`, rather than an arbitrary per-module judgment call
* Good, because it prevents a plausible-looking "fix" (typing up `IConfig`) that would actually
  collapse the distinction this repo relies on elsewhere between generic and dedicated
  interfaces, without gaining any real type safety — callers of a tightened `IConfig` would
  still be passing a `name: str`, just alongside a narrower value type
* Bad, because the framework requires judgment per config value — there's no mechanical check
  that flags "this belongs on a typed interface, not `IConfig`"; it relies on whoever adds the
  config value recognizing which bucket it falls into
* Neutral, because this decision doesn't touch `IConfig`'s code at all — it only records why the
  code stays as it is, for the next time someone reads it and assumes otherwise
