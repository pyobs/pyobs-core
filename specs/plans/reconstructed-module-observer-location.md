# Plan: Module observer-location capabilities (reconstructed)

*Reconstructed after the fact from `specs/design/module_observer_location.md` and commit
`2c4404b0` — written after the change landed, not before it.*

## Goal

Let other modules/clients query a remote module's configured observatory location over comm.
Every `Module` already knows its own location locally (`Object._location`/`_observer`/
`_timezone`), but it was purely local — nothing published it, so each config that needed a
location repeated the block rather than reading it from a peer.

## Architecture

Location is static for a module's lifetime, so it publishes via the existing one-shot
**capabilities** mechanism (same as `ModuleCapabilities`'s version/label), not the pub-sub
**state** mechanism used for values that change — this also sidesteps the class of bug fixed in
`specs/adrs/0001-interface-state-checked-by-own-declaration-not-inheritance.md` (a widely
implemented interface picking up unwanted state and causing phantom XMPP subscriptions).
`Interface.capabilities` is a single `ClassVar` slot per interface, so location is added as a
nested `ModuleLocation` field inside `ModuleCapabilities` rather than a sibling dataclass.
`_on_module_opened` — which already fires for every connecting peer and already fetches its
`IModule` capabilities to compare pyobs versions — is the natural, automatic, system-wide place
to also compare location: if both sides have one configured, geocentric distance is computed
via `EarthLocation`, and a warning fires if it exceeds 100m. This is a backstop for config
drift (pyobs has no shared "site" concept; two modules at the same observatory could disagree
via typo/copy-paste), not a replacement for the existing `{include}`/YAML-anchor mechanism
that shares a `location:` block across configs.

## File Map

| File | Change |
|---|---|
| `pyobs/interfaces/IModule.py` | New `ModuleLocation` dataclass, nested `location: ModuleLocation \| None` field on `ModuleCapabilities` |
| `pyobs/interfaces/__init__.py` | Export `ModuleLocation` |
| `pyobs/modules/module.py` | `Module.open()` publishes `location=ModuleLocation(...)` (or `None`); `_on_module_opened` compares peer location, warns past 100m |
| `tests/comm/test_presence.py` | Test coverage |
| `CHANGELOG.rst` | Entry for the change |

## Tasks

- [x] Write design doc (`specs/design/module_observer_location.md`, originally
      `DESIGN_module_location.md`)
- [x] Add `ModuleLocation` dataclass, nested in `ModuleCapabilities`
- [x] Publish location from `Module.open()` (or `None` if unconfigured)
- [x] Compare peer location in `_on_module_opened`, warn past 100m geocentric distance
- [x] Add test coverage
- [x] Fold design doc into `DEVELOPMENT.md` on landing (now split back out to
      `specs/design/` instead, per the new persistent-design-doc convention)
