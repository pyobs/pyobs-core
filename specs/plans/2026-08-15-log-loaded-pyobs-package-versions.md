# Plan: Log the loaded pyobs-* package versions at module startup

Status: implemented

## Problem

A running pyobs module imports more than pyobs-core: a `FliCamera` pulls in `pyobs-fli` too, and
the exact set depends on the module's config. There is currently no single place that records
*which* versions of *which* pyobs packages a given process actually loaded. `Module.get_version()`
returns only pyobs-core's own version (`pyobs/modules/module.py:427`), and it is published to comm
as `ModuleCapabilities(version=...)` (`module.py:355`), never written to the log/journal.

The concrete motivation is pyobs-web-admin: it wants to answer "which versions is this module
actually running right now?" per module. It reads logs (flat file or journald) but does not speak
comm, and a comm-less module (`httpfilecache`) has no comm channel at all. A startup log line is the
comm-independent signal it can consume.

## Decision

Log one line at module startup listing every *loaded* `pyobs`-prefixed distribution and its
version, sourced from `importlib.metadata`. Not `single_source`, and no per-package `version()`
methods.

Why `importlib.metadata` and not `single_source`/`version()`:

- Every core-tier package already declares a static `version = "..."` in its `pyproject.toml`
  (e.g. `pyobs-fli` `2.0.0.dev7`, `pyobs-asi` `2.0.0.dev4`), which is what ends up in the installed
  `.dist-info/METADATA`. `importlib.metadata.version(dist)` reads exactly that, with zero changes to
  the driver repos.
- `single_source` + `pyobs/version.py` is a *runtime API* for pyobs-core specifically: it feeds the
  comm capabilities and the cross-module mismatch check (`module.py:447-482`), and derives the
  version from git in dev checkouts. Replicating it into every driver would be busywork and would
  introduce a second, potentially divergent version source (git-derived vs. installed).
- `importlib.metadata` is uniform: every package, pyobs-core included, comes from the same source.

Scope: all `pyobs`-prefixed distributions, discovered by import (not a hardcoded fleet list), so
new packages are picked up automatically. The GUIs (`pyobs-gui`, `pyobs-polaris`, `pyobs-web-client`)
are out of scope per `specs/steering/pyobs-project-tiers.md` — but the import-based filter will
naturally include `pyobs-gui` if it is ever loaded, which is fine, not something to special-case.

## Design

### Helper

New module `pyobs/utils/versions.py`:

```python
def loaded_pyobs_packages(sys_modules=None) -> dict[str, str]:
    ...
```

- Build the top-level import name -> distribution names map via
  `importlib.metadata.packages_distributions()` (this already handles the underscore/hyphen split:
  `pyobs_fli` -> `pyobs-fli`, `pyobs` -> `pyobs-core`).
- For each top-level name present in `sys.modules` (default `sys.modules`), resolve its
  distributions and keep the ones whose name starts with `pyobs`.
- Read each version via `importlib.metadata.version(dist)`, skipping `PackageNotFoundError`
  defensively.
- Return `{dist: version}` sorted by name.

`sys_modules` is a parameter so the function is pure and unit-testable without patching
`sys.modules`.

### Log point

In `pyobs/application.py`, `Application._main`, immediately before `await self._module.startup()`
(`application.py:378`):

```python
pkgs = loaded_pyobs_packages()
log.info("Loaded pyobs packages: %s", ", ".join(f"{k}={v}" for k, v in pkgs.items()))
```

This is the one place after *both* module-construction paths have finished importing everything:
the config path builds the module in `Application.__init__` (`application.py:262`,
`self._module = get_object(cfg, Module)`, which recursively imports the module class and every
child object/driver), and the factory path builds it in `_main` (`application.py:373`). By line
378 `sys.modules` holds the complete set for either path, including a `MultiModule`'s children
(constructed in `MultiModule.__init__`).

The line goes through the already-configured handlers (`basicConfig` runs at `application.py:200`),
so it reaches the flat file and journald alike, tagged with the module name (`PYOBS_MODULE`). Under
`MultiModule` it is process-wide and tagged `multi` — acceptable, since the version set is a
process fact, not a per-child fact.

## Out of scope (follow-ups)

- pyobs-web-admin parsing this line to display a per-module "running version" — a separate change in
  the web-admin repo.
- Modules started before this ships have no such line; web-admin should treat "no line" as
  "unknown", not "current".
- Cleaning up `dbus-next` (a declared but unused dependency, `pyproject.toml:18`) — unrelated to
  this feature, flagged here only because it surfaced while investigating a local RPC idea that was
  abandoned.

## Open questions

None blocking. One cosmetic choice: single comma-joined line (chosen) vs. a more rigid key=value
format for machine parsing. The comma-joined `name=version` form is both human-readable and easy to
split, so it's fine for the follow-up consumer too.

## Implementation checklist

- [x] Add `pyobs/utils/versions.py` with `loaded_pyobs_packages(sys_modules=None)`.
- [x] Log the line in `Application._main` before `startup()`.
- [x] Unit-test the helper: fake `sys_modules` containing `pyobs` and `pyobs_fli`, assert the
      filtered, sorted `{dist: version}` result and that non-`pyobs` modules are excluded.
- [x] Run the pyobs-core test suite (`.venv/bin/pytest`); confirm no regressions.
- [x] Update this doc's `Status:` to `implemented` once landed.
