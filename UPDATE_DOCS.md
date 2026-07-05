# Sphinx docs sweep — findings (2026-07-05)

Full pass over every prose page under `docs/source/` (autodoc-only stub pages, i.e. pages that
are just `.. automodule::`/`.. autoclass::` lists with no hand-written prose, were originally
skipped on the assumption they self-update from docstrings — that assumption turned out to be
wrong for two of them, see Priority 1 below). Findings are checked against the actual current
code (`pyobs/...`), not just against `DEVELOPMENT.md`'s own narrative, and cross-checked with a
real `sphinx-build -E` run after every fix.

## Priority 1 — broken references (autodoc errors) — ✅ done

Everything below was confirmed broken via `sphinx-build` (`ModuleNotFoundError`/`AttributeError`/
`ref.class not found`) and is now fixed and re-verified with a clean rebuild.

- [x] `docs/source/api/interfaces.rst` — removed the dead `ILatLon` section.
- [x] `pyobs.robotic.filesystem` / `pyobs.robotic.backend` / `pyobs.robotic.lco` → all moved to
  `pyobs.robotic.storage.{filesystem,backend,lco}`. Fixed in `api/robotic/index.rst`,
  `api/robotic/scheduling.rst`, `recipes/robotic.rst`, `config_examples/iag50cm.rst`.
- [x] `pyobs.robotic.lco.LcoTaskSchedule` (config_examples/iag50cm.rst) → confirmed via git
  history (`07e93158`, `ea95dd0e`) this class was renamed to `LcoObservationArchive` when the
  robotic subsystem's backend abstraction was introduced. Fixed both YAML instances and both
  prose `:class:` refs.
- [x] `pyobs.robotic.taskarchive`/`observationarchive` → `pyobs.robotic.storage.taskarchive`/
  `observationarchive`, including one instance in `scheduling.rst` (~line 397) that wasn't in
  the original punch list.
- [x] `api/robotic/scripts.rst` "Built-in scripts" section — all renamed/relocated:
  `AutoFocus`→`imaging.autofocus.AutoFocusScript`, `DarkBias`→`calibration.darkbias.DarkBiasScript`,
  `SkyFlats`→`calibration.skyflats.SkyFlatsScript`, `SequentialRunner`/`ParallelRunner`/
  `ConditionalRunner`/`CasesRunner`/`SelectorScript` → moved under `control.*` (names kept),
  `CallModule`→`utils.callmodule.CallModuleScript`, `LogRunner`→`utils.log.LogScript`. Also fixed
  the matching `pyobs.robotic.scripts.SkyFlats` reference in `config_examples/iag50cm.rst`'s
  `skyflats:` block, and the `LcoDefaultScript`/`LcoAutoFocusScript`/`LcoScript` paths in the same
  file (`pyobs.robotic.lco.scripts.*` → `pyobs.robotic.storage.lco.scripts.*`). One dangling
  `:class:` ref to `LcoDefaultScript` (never had an `autoclass` entry anywhere, even before these
  fixes) was downgraded to plain code text rather than a broken cross-reference.
  **Not done**: adding the 4 new undocumented classes (`ImagingScript`, `TransitImagingScript`,
  `PointingScript`, `DebugTriggerScript`) — that's new content, not a broken-reference fix.
- [x] `docs/source/api/comm.rst` — removed the fictional `pyobs.comm.dbus.DbusComm` (never
  existed). Added missing `autoclass` entries for `LocalComm`/`DummyComm`, which were referenced
  in the backend table via `:class:` but had no matching `autoclass` anywhere, so the
  cross-references were dangling too.
- [x] **Found mid-fix, not in the original list**: `docs/source/api/utils/archive.rst` and
  `docs/source/api/utils/skyflats.rst` are *entirely* built around `pyobs.utils.archive`/
  `pyobs.utils.skyflats`, which don't exist — that whole subtree moved to
  `pyobs.robotic.utils.archive`/`pyobs.robotic.utils.skyflats` back in **v1.44** (2025-04-24,
  pre-2.0). These were wrongly assumed "self-updating" in the original sweep since they're pure
  autodoc stubs; fixed both files (including two section-header underline lengths that needed
  adjusting after the title text got longer).
- [x] `docs/source/config_examples/iag50cm.rst` — same pre-2.0 `pyobs.utils.skyflats.*` /
  `pyobs.utils.archive.*` staleness as above (originally filed under Priority 3), fixed alongside
  the rest of this file's LCO path fixes.

Verified with `rm -rf` + `sphinx-build -E` (clean, no cached doctrees): zero
`ModuleNotFoundError`/`AttributeError`/dangling `ref.class` warnings remain **except** the two
items below, which are a different kind of problem.

### Resolved by deletion (per explicit instruction — both features are gone for good)

Both are real, *intentional*, already-committed code removals (confirmed via
`git log --diff-filter=D`), not renames — so there was no "correct path" to swap in.

- [x] **`docs/source/recipes/simulation.rst`** — deleted the "Connecting telescope and camera"
  section (`MultiModule` + `pyobs.utils.simulation.SimWorld`/`SimTelescope`/`SimCamera`), removed
  outright in `a36ff5a0` with no replacement. This recipe was incorrectly marked "confirmed not
  stale" in the original sweep (only checked for proxy/interface staleness, not deleted modules).
- [x] **`docs/source/api/robotic/scripts.rst`** — deleted the "TargetPicker" section
  (`pyobs.robotic.utils.TargetPicker`, removed in `b76e9ef2`). Superseded by `DynamicTarget`
  (`pyobs.robotic.scheduler.targets.dynamictarget.DynamicTarget`) + the `Picker`/`CsvPicker`
  classes (`pyobs.robotic.scheduler.targets.picker`), added in v1.46. **Note**: none of
  `DynamicTarget`/`Picker`/`CsvPicker` are documented anywhere currently — not added here since
  it's new content rather than a fix, but flagging as a gap for whenever the scheduling docs get
  their next pass.
- [x] **Found while cleaning up the above**: `docs/source/api/utils/simulation.rst` was a whole
  dedicated autodoc page for the same deleted `pyobs.utils.simulation` module — deleted the page
  and its `api/utils/index.rst` toctree entry. Also removed one dangling
  `:class:`~pyobs.utils.simulation.SimWorld`` reference in `api/utils/time.rst`'s prose.

All four confirmed clean via `rm -rf` + `sphinx-build -E`: zero `ModuleNotFoundError`/
`AttributeError`/dangling `ref.class` warnings remain from any 2.0-era rename or removal.

## Priority 2 — stale `Proxy` usage (teaches code that no longer works)

Not yet started. `Proxy` is `async with`-only now (see `docs/source/whatsnew-2.0.rst`);
`await self.proxy(...)` / `await self.comm.proxy(...)` returning a usable object is gone.

- [ ] `docs/source/api/comm.rst` — lines 40, 43, 50–54 (`telescope = await self.proxy(...)`,
  `safe_proxy` example)
- [ ] `docs/source/api/module.rst` — lines 87, 101
- [ ] `docs/source/overview.rst` — line 100 (the rest of this page, notably the whole "Access
  control" section, is already up to date — this looks like a leftover missed during that pass)
- [x] `docs/source/api/robotic/scripts.rst` — the `can_run`/`run` example (was lines 34–35,
  44–45) — fixed as part of the Priority 1 pass on this file since it was in the same block as
  the script renames; converted to `has_proxy`/`AsyncExitStack`, matching the pattern already
  used in `recipes/robotic.rst`.
- [ ] `docs/source/api/robotic/serialization.rst` — line 100 (single instance, otherwise this
  page is current — already uses `PolymorphicBaseModel`, not the old `SubClassBaseModel` name)
- [x] `docs/source/recipes/robotic.rst` — fixed (was lines 108–109, 118–119): `can_run` now uses
  `self.comm.has_proxy(...)`, `run` uses `AsyncExitStack` since both proxies are used together
  for the rest of the method (matches the pattern documented in `whatsnew-2.0.rst`).
- [ ] `docs/source/recipes/jupyter.rst` — the whole "Usage" section (lines ~148–235) needs a
  rewrite, not just a proxy-pattern fix: it also calls `telescope.get_radec()` /
  `telescope.get_altaz()` (line 166), both **removed** methods (replaced by
  `IPointingRaDec.state`/`IPointingAltAz.state`). This is the most out-of-date single doc in
  the tree — every code cell from "Telescope" onward assumes 1.x semantics.

(The `recipes/robotic.rst` and `api/robotic/scripts.rst` proxy fixes got done opportunistically
while both files were open for Priority 1 edits — not a signal to start Priority 2 broadly yet.)

## Priority 3 — pre-existing (non-2.0) staleness surfaced along the way — ✅ done

- [x] `docs/source/config_examples/iag50cm.rst` and `docs/source/api/utils/{archive,skyflats}.rst`
  — see Priority 1 above, folded in since they were mechanically identical fixes.

## Priority 4 — documentation gap, not an error

- [ ] `docs/source/project/changelog.rst` just does `.. include:: ../../../CHANGELOG.rst`, and
  `CHANGELOG.rst` itself stopped being updated after **v1.47.0** (2025-06-07) — everything from
  v1.48 through v1.53.x and the entire `v2.0.0.dev1`–`dev11` series (315 commits) has no
  changelog entry at all. `whatsnew-2.0.rst` now covers the highlights of the 2.0 portion of that
  gap, but the changelog itself is still silently frozen. Worth deciding whether to resume
  updating `CHANGELOG.rst` per-release, backfill it, or intentionally deprecate it in favor of
  `whatsnew-2.0.rst` + GitHub releases.

## Confirmed NOT stale — already updated for 2.0, no action needed

- `docs/source/overview.rst` — has a full, accurate "Access control" section describing the
  `acl:` block (matches current `Module._parse_acl` exactly). Only the one proxy-pattern leftover
  above needs fixing.
- `docs/source/installing.rst`, `docs/source/cli.rst` — already document the `pyobs.yaml` config
  file lookup order and `--syslog`.
- `docs/source/development.rst` — already states Python 3.11 as the base version.
- `docs/source/quickstart.rst` — no proxy calls, no removed interfaces touched.
- `docs/source/api/object.rst` — no proxy usage, unaffected by any of the 2.0 changes.
- `docs/source/api/robotic/serialization.rst` — `PolymorphicBaseModel` rename already applied
  correctly (aside from the one proxy line above).
- `docs/source/api/interfaces.rst`, `docs/source/api/events.rst` — pure autodoc listings; content
  is pulled from current docstrings automatically, so nothing to hand-edit beyond the `ILatLon`
  removal already done.
- `docs/source/addmod/index.rst`, `docs/source/modules/index.rst`, `docs/source/api/index.rst` —
  pure toctrees/external links, nothing to update.

## Not checked in this pass

- `docs/source/api/image_processors/*.rst`, `docs/source/modules/*.rst`,
  `docs/source/api/utils/*.rst` other than `archive.rst`/`skyflats.rst` — all pure autodoc stubs.
  Given that two of this exact category turned out to be broken, these are no longer a safe
  "assumed fine" — worth at minimum a `sphinx-build -E` diff check, which is cheap, even if a
  full manual read isn't.
