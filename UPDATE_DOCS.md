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

## Priority 2 — stale `Proxy` usage (teaches code that no longer works) — ✅ done

`Proxy` is `async with`-only now (see `docs/source/whatsnew-2.0.rst`); `await self.proxy(...)` /
`await self.comm.proxy(...)` returning a usable object is gone.

- [x] `docs/source/api/comm.rst` — the `self.proxy(...)`/`await telescope.move_radec(...)` example
  and the `safe_proxy` example both converted to `async with ... as x:`. `safe_proxy` now yields
  `None` inside the block rather than returning `None` directly (verified against
  `Comm.safe_proxy`'s actual docstring: "Same as proxy(), but yields None inside the block instead
  of raising").
- [x] `docs/source/api/module.rst` — both examples converted (the `MyCamera`/`grab_data` one and
  the `open()`/`move_radec` one).
- [x] `docs/source/overview.rst` — the "Communication between modules" example converted.
- [x] `docs/source/api/robotic/scripts.rst` — the `can_run`/`run` example — fixed as part of the
  Priority 1 pass on this file since it was in the same block as the script renames; converted to
  `has_proxy`/`AsyncExitStack`, matching the pattern already used in `recipes/robotic.rst`.
- [x] `docs/source/api/robotic/serialization.rst` — the `PrivateAttrMixin` example converted.
- [x] `docs/source/recipes/robotic.rst` — `can_run` now uses `self.comm.has_proxy(...)`, `run`
  uses `AsyncExitStack` since both proxies are used together for the rest of the method (matches
  the pattern documented in `whatsnew-2.0.rst`).
- [x] `docs/source/recipes/jupyter.rst` — full rewrite of the "Usage" section, not just a
  proxy-pattern fix. It also called `telescope.get_radec()`/`telescope.get_altaz()`, both
  **removed** methods — replaced with `await telescope.wait_for_state(IPointingRaDec)` /
  `wait_for_state(IPointingAltAz)` (verified `RaDecState`/`AltAzState` field names against
  `pyobs/interfaces/IPointingRaDec.py`/`IPointingAltAz.py`). Also restructured so each cell
  re-resolves its proxy via a fresh `async with` block rather than holding `telescope =`/
  `camera =` across cells — added a short prose note explaining why (a held reference can go
  stale across a reconnect between cells; a proxy resolved just before use is guaranteed current).
  The camera cell now does exposure-time/image-type setup and `grab_data` inside one `async with`
  block since they're used together; `img = await vfs.read_image(...)` stays outside it, unrelated
  to the proxy.

Verified via clean `sphinx-build -E`: no rendering regressions in the edited files (RST literal
blocks with nested `async with`/indentation all render correctly), and no remaining
`await self.proxy(...)`/`await self.comm.proxy(...)`/`await comm.proxy(...)` in any doc page except
`whatsnew-2.0.rst`, where it's intentionally shown as the old, no-longer-working pattern.

## Priority 3 — pre-existing (non-2.0) staleness surfaced along the way — ✅ done

- [x] `docs/source/config_examples/iag50cm.rst` and `docs/source/api/utils/{archive,skyflats}.rst`
  — see Priority 1 above, folded in since they were mechanically identical fixes.

## Priority 4 — CHANGELOG.rst gap — ✅ done (backfilled)

`CHANGELOG.rst` had stopped being updated after **v1.47.0** (2025-06-07) — everything from v1.48
through v1.53.x and the entire `v2.0.0.dev1`–`dev11` series had no entry. Decision (explicit):
backfill it now from git history, then resume per-release going forward.

- [x] Backfilled 17 new version sections at the top of `CHANGELOG.rst`, above the existing
  `v1.47.0` entry: `v1.48.0` through `v1.53.0` (the six 1.x minor releases), then
  `v2.0.0.dev1` through `v2.0.0.dev10`, then `v2.0.0.dev11 (unreleased)` covering everything up to
  current `HEAD` (matches the in-progress version already in `pyproject.toml`).
- [x] **Patch releases excluded from their own headings**, per explicit instruction — `v1.49.1`
  and `v1.52.1`–`v1.52.18` (19 patch tags) don't get their own sections; their actual commits are
  still represented, folded into whichever minor-version section they chronologically fall under
  (e.g. `v1.49.1`'s changes are in the `v1.50.0` entry, since that's the next minor boundary).
  `v1.53.1`/`v1.53.2` similarly excluded (their commits weren't found on this branch's linear
  history at all — they look like they were cut from a separate maintenance branch — so there was
  nothing of theirs to fold in regardless).
- [x] Dev pre-releases (`v2.0.0.dev1`–`dev11`) got their own sections rather than being
  consolidated, since they're not "patch" releases by version number and each one is a real,
  distinct git tag in this project's history — including a few with very little content
  (`dev4`, `dev5`, `dev7`–`dev9` each cover only 1-3 commits). Flagging this in case a coarser
  grouping (e.g. one combined "dev" entry) is preferred instead.
- [x] Content was synthesized from `git log` commit subjects across the full range (~470 commits),
  cross-checked against actual diffs (`git show --stat`/full diff) for anything ambiguous, and
  cross-checked against `whatsnew-2.0.rst` for the 2.0 portion for consistency. This is a curated
  summary matching the existing changelog's own voice/density (e.g. `v1.47.0` has 6 bullets for
  27 commits) — it is **not** a verbatim commit-by-commit transcription. Pure-internal noise
  (`fixed tests`, `added tests`, `make mypy happy`, individual `type: ignore` commits, individual
  Dependabot bumps) was deliberately omitted or rolled up, consistent with how the rest of the
  file already reads.
- [x] Verified underline lengths (`*` matching title length exactly, this file's own convention)
  for all 17 new headings, and confirmed via clean `sphinx-build -E` that `project/changelog.rst`
  renders the new content with zero new warnings (the only remaining "Title underline too short"
  warnings are three pre-existing ones in the untouched `v1.10.0`–`v1.12.0` entries, unrelated to
  this change).
- [x] **Enforcement added**: `scripts/check_changelog.sh`, wired into `.github/workflows/pypi.yml`
  as a step before build/publish. Fails a tagged release if it's a minor/major bump or a
  `.devN` pre-release and `CHANGELOG.rst` has no matching heading; patch releases (`X.Y` unchanged,
  no `.dev` involved) are exempt. Resolves "the previous release" via the tag's own commit
  ancestry (`git describe --tags --abbrev=0 TAG^`) rather than a global version sort, since this
  project has cut a patch release from an older maintenance branch after newer tags already
  existed elsewhere (`v1.53.1`/`v1.53.2` postdate several `v2.0.0.dev*` tags) — a naive
  highest-tag-wins comparison would misidentify the predecessor in that case. Verified against
  real tag history and a synthetic repo modeling that exact parallel-branch scenario.

## Confirmed NOT stale — already updated for 2.0, no action needed

- `docs/source/overview.rst` — has a full, accurate "Access control" section describing the
  `acl:` block (matches current `Module._parse_acl` exactly); the one proxy-pattern leftover it
  had is fixed now too (Priority 2).
- `docs/source/installing.rst`, `docs/source/cli.rst` — already document the `pyobs.yaml` config
  file lookup order and `--syslog`.
- `docs/source/development.rst` — already states Python 3.11 as the base version.
- `docs/source/quickstart.rst` — no proxy calls, no removed interfaces touched.
- `docs/source/api/object.rst` — no proxy usage, unaffected by any of the 2.0 changes.
- `docs/source/api/robotic/serialization.rst` — `PolymorphicBaseModel` rename already applied
  correctly; the one proxy line it had is fixed now too (Priority 2).
- `docs/source/api/interfaces.rst`, `docs/source/api/events.rst` — pure autodoc listings; content
  is pulled from current docstrings automatically, so nothing to hand-edit beyond the `ILatLon`
  removal already done.
- `docs/source/addmod/index.rst`, `docs/source/modules/index.rst`, `docs/source/api/index.rst` —
  pure toctrees/external links, nothing to update.

## Autodoc sanity check on the remaining stub pages — ✅ done, nothing broken

Given `archive.rst`/`skyflats.rst` turned out broken despite being pure autodoc stubs (see
Priority 1 above), ran the same class of check over every remaining stub page
(`api/image_processors/*.rst`, `modules/*.rst`, `api/utils/*.rst` other than
`archive.rst`/`skyflats.rst`, which were already fixed):

- Extracted all 151 `automodule`/`autoclass`/`autofunction`/`autodata` dotted paths across those
  files and imported each one in Python — all resolve.
- Extracted all `:class:`/`:meth:`/`:func:`/`:mod:`/`:attr:`/`:exc:` cross-reference roles used in
  any hand-written prose in those files (7 unique targets) — all resolve.
- Grepped all of them for plain-text mentions of every symbol confirmed renamed/removed elsewhere
  in this sweep (`pyobs.utils.{simulation,skyflats,archive}`, `pyobs.robotic.{lco,filesystem,
  backend,taskarchive,observationarchive}` without `.storage.`, `ILatLon`, `SubClassBaseModel`,
  `MeritScheduler`, `await self.proxy(`, `cache_proxies`, `DbusComm`, `get_radec()`, `get_altaz()`,
  `get_cooling()`, `get_motion_status()`) — zero hits.

No changes needed to any of these files.

## Follow-up content gaps — ✅ done

Two gaps flagged earlier as "new content, not a fix" and deliberately left out of the Priority 1
pass — closed now on request:

- [x] **`docs/source/api/robotic/scheduling.rst`** — documented `DynamicTarget` and the
  `Picker`/`CsvPicker` classes (`pyobs.robotic.scheduler.targets.{dynamictarget,picker}`) in the
  "Targets" section, with a YAML example, replacing the coverage lost when `TargetPicker` was
  deleted. Also added `HelioprojectiveRadialTarget`, found undocumented in the same package
  (`pyobs/robotic/scheduler/targets/__init__.py`) while doing this — not originally asked for, but
  directly adjacent and trivial to include.
- [x] **`docs/source/api/robotic/scripts.rst`** — documented the 4 previously-undocumented script
  classes: `ImagingScript` and `TransitImagingScript` (added to "Observing", `ImagingScript` is
  the actual default script for science exposures), `PointingScript` (added to "Observing", next
  to `SkyFlatsScript` since it points the telescope for flat-fielding), and `DebugTriggerScript`
  (added to "Control flow", next to `LogScript` — it's a minimal test/debug helper, not a real
  observing script).

All dotted paths verified importable, and confirmed via clean `sphinx-build -E` that both pages
render the new content with zero new warnings (a handful of pre-existing, unrelated warnings in
these same files — duplicate autosectionlabels, a couple of dangling `:meth:`/`:exc:` refs in
untouched prose — were already there before this change).
