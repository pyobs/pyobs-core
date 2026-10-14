# Write a task's constraints and priorities into the FITS header

Status: implemented (2026-10-13). Deviation from the plan, on Tim's request: the base `Constraint` builds
the cards (`req_token` class variable plus `req_fields()`), so the subclasses do not import
`FitsHeaderEntry` and only declare their values; `get_fits_headers(index)` stays on the base class and
can still be overridden. The `_req_token` helper of the plan is gone.

Follow-up 2026-10-14 (#962): merged to develop in PR #974 (`a60e8ccb`), not yet released. Solar bounds at
-90 degrees minimum or +90 degrees maximum impose no limit and are omitted from the header.
Effective defaults (maximum -18 degrees) and the direction card are retained.

Repos: pyobs-core

## Context

#962 parts 6, 7 and 9. Part 8 (the scheduler's merit) needs a portal change and has its own plan,
`2026-10-13-fits-header-scheduler-merit.md`. Checked against `develop` (`93876735`); line numbers
below are for that commit. Marks: **[code]** read from code, **[inferred]** follows from code but
not tested, **[unverified]** not checked.

The reporter runs several piers off one portal with a custom planner and wants each frame to carry
what it was asked for and how it was ranked, because tasks are edited in place in the portal and
cannot be looked up later through `REQNUM`.

Today **[code]**:

- `Mastermind.get_fits_header_before` (`pyobs/modules/robotic/mastermind.py:324-348`) returns
  `{}` outside a run. During a run it starts from `self._task.get_fits_headers()` (the running
  script's headers, `pyobs/robotic/task.py:110-121`), adds `TASK`, `REQNUM`, `PROJECT` (if set) and
  `OBSNUM` (if set), then the `HIERARCH <MODULE> VERSION <PACKAGE>` cards (`mastermind.py:345`).
- The mastermind keeps `self._task` and `self._obsnum` while a task runs (set at
  `mastermind.py:260-262`, cleared after failure and after finishing), not the observation.
- `Task.priority: float | None`, default 1.0, range 0 to 9999 (`task.py:44`);
  `Task.constraints: list[Constraint]` (`task.py:45`); `Project.priority: float | None`
  (`task.py:161`).
- `Constraint` (`pyobs/robotic/scheduler/constraints/constraint.py:21`) is a pydantic model with
  `to_astroplan()` and `__call__()`; nothing about FITS. Built-in subclasses and their fields:

  | Class | File:line | Fields |
  |---|---|---|
  | `AirmassConstraint` | `airmassconstraint.py:19-24` | `max_airmass` (1.0 to 9.9) |
  | `MoonSeparationConstraint` | `moonseparationconstraint.py:20-25` | `min_distance` (deg, 0 to 180) |
  | `MoonIlluminationConstraint` | `moonilluminationconstraint.py:17-21` | `max_phase` (fraction, 0 to 1) |
  | `SolarElevationConstraint` | `solarelevationconstraint.py:23-28` | `min_elevation`, `max_elevation` (deg), `direction` (`"rising"`, `"setting"`, `"both"`) |
  | `TimeConstraint` | `timeconstraint.py:19-23` | `start`, `end` (`AstroPydanticTime`) |

- `FitsHeaderEntry` is `value: int | float | str | None`, `comment: str`
  (`pyobs/interfaces/IFitsHeaderBefore.py:11-13`).
- `version_fits_headers` (`pyobs/utils/versions.py:64-80`) already uses HIERARCH cards with empty
  comments because a comment overflows the 80-char card (`versions.py:73-75`).

## Decisions (given, not reopened)

- HIERARCH cards with prefix `REQ`, short or empty comments.
- Each `Constraint` class declares its cards via `get_fits_headers(index: int) ->
  dict[str, FitsHeaderEntry]`. The base returns `{}`, so plugin constraints write nothing until they
  opt in. The mastermind loops `task.constraints` and counts per type for the index.
- Names:

  | Card | Source |
  |---|---|
  | `HIERARCH REQ PRIORITY` | `Task.priority` |
  | `HIERARCH REQ PROJECT PRIORITY` | `Project.priority` from the task archive |
  | `HIERARCH REQ MERIT` | scheduler merit (other plan) |
  | `HIERARCH REQ AIRMASS MAX` | `AirmassConstraint.max_airmass` |
  | `HIERARCH REQ MOONDIST MIN` | `MoonSeparationConstraint.min_distance` (deg) |
  | `HIERARCH REQ MOONFRAC MAX` | `MoonIlluminationConstraint.max_phase` (fraction) |
  | `HIERARCH REQ SUNALT MIN` / `MAX` / `DIR` | `SolarElevationConstraint.min_elevation` / `max_elevation` / `direction` |
  | `HIERARCH REQ TIME START` / `END` | `TimeConstraint.start` / `end` (ISO) |

- A second constraint of the same type gets a number on the type token: `HIERARCH REQ SUNALT2 MAX`,
  `SUNALT3 MAX`. The first has no number.
- The existing top-level `REQNUM` card is a different key; no clash.
- Written in `Mastermind.get_fits_header_before`, next to `TASK`/`REQNUM`/`PROJECT`/`OBSNUM`.

### Why the mastermind, not `Task.get_fits_headers`

**[code]** `Task.get_fits_headers` only forwards the running script's headers (`task.py:110-121`)
and returns `{}` when no script runs. Scripts also run outside a mastermind (e.g. `ScriptRunner`),
where there is no request. The mastermind is the one place that has the task, the task archive
(project priority), the observation (merit, other plan) and already writes the request cards. So
the request cards belong there, as #962 part 9 asks.

## Where each value comes from at header time

- **Task priority** **[code]**: `self._task.priority`. `None` means "no priority": omit the card.
- **Constraints** **[code]**: `self._task.constraints`, the list of the task object captured at
  task start (`mastermind.py:260`). **[inferred]** The portal task archive replaces its task objects
  when a task is edited (`pyobs/robotic/storage/portal/taskarchive.py:125`, `_update`), but the
  mastermind keeps its own reference, so the cards describe the task as it was when the run
  started. That is what the reporter wants.
- **Project priority**:
  - **[code]** The mastermind has `self._task_archive` only if configured with `tasks:`
    (`mastermind.py:71`); otherwise there is no project priority. Omit the card.
  - **[code]** `PortalTaskArchive.get_projects()` returns a cached list (`portal/taskarchive.py:181-187`),
    refreshed by a 5 s background poll when `auto_update=True`, the default
    (`portal/taskarchive.py:20,41-42,73`). `LcoTaskArchive.get_projects()` is cached the same way
    (`lco/taskarchive.py:82-84`), `MemoryTaskArchive` returns its list (`memory/taskarchive.py:30-32`).
    No HTTP call per header.
  - **[code]** `FilesystemTaskArchive.get_projects()` raises `NotImplementedError`
    (`filesystem/taskarchive.py:35-41`). Catch it and omit the card.
  - **[code]** A `PortalTaskArchive` with `auto_update=False` has an empty project list.
  - Proposal: look the project up **once at task start** (where `_task` is set) and keep the
    priority in `self._project_priority`, so all frames of one run carry the same value and header
    calls do no work. No extra cache needed.
- **Other task types** **[code]**: `LcoTask` builds constraints from the LCO request
  (`pyobs/robotic/storage/lco/task.py:71-94`): one `TimeConstraint` per window (`task.py:76-77`, so
  numbering matters), `AirmassConstraint`, `MoonSeparationConstraint`,
  `MoonIlluminationConstraint`, and `SolarElevationConstraint(max_elevation=-18.0)` (`task.py:85-92`). Its
  priority is `ipp_value * tac_priority` (`lco/taskarchive.py:120`), and its project priority is
  `tac_priority` (`lco/taskarchive.py:128`), so for LCO tasks `REQ PRIORITY` already contains the
  project priority. Filesystem and memory tasks are plain `Task`s with whatever the YAML or caller
  set.

## Value formatting

| Card | Value written |
|---|---|
| `PRIORITY`, `PROJECT PRIORITY` | `float` as stored |
| `AIRMASS MAX`, `MOONDIST MIN`, `MOONFRAC MAX`, `SUNALT MIN`, `SUNALT MAX` | `float(field)` |
| `SUNALT DIR` | the string `"rising"`, `"setting"` or `"both"` |
| `TIME START`, `TIME END` | `Time.isot` in UTC, e.g. `"2026-10-13T20:15:00.000"` |

- No rounding: the cards are for analysis, and Python's float repr is short for typical values.
- `SUNALT` bound cards are written only for effective bounds: omit `MIN` -90 and `MAX` +90.
  The effective default `MAX` -18 and the `DIR` card (including `"both"`) are retained.
- Comments: units where they help and fit (`"deg"`, `"fraction"`), otherwise empty.
- No task constraints: no constraint cards. Priority `None`: no `REQ PRIORITY` card. No project or
  project priority `None`: no `REQ PROJECT PRIORITY` card.

## Proposed changes

- [ ] **`Constraint.get_fits_headers(self, index: int) -> dict[str, FitsHeaderEntry]`** in
      `constraint.py`, returning `{}`. Docstring: `index` is 1 for the first constraint of this
      type in a task, 2 for the second, and so on; use `self._req_token(token, index)` to build the
      key.
- [ ] **Helper** `Constraint._req_token(token: str, index: int) -> str` (or a module function):
      returns `token` for index 1, `f"{token}{index}"` otherwise. Keys are built as
      `f"HIERARCH REQ {self._req_token('SUNALT', index)} MAX"`.
- [ ] **Override in the five built-in classes**, with the cards from the table above.
- [ ] **`Mastermind`**:
  - [ ] new `self._project_priority: float | None`, set at task start next to `self._task`
        (`mastermind.py:260-262`) via a small `_lookup_project_priority(task)` that returns `None`
        without a task archive, on `NotImplementedError`, if the project isn't found, or if its
        priority is `None`; cleared wherever `self._task` is cleared.
  - [ ] in `get_fits_header_before`, after `OBSNUM`: `REQ PRIORITY`, `REQ PROJECT PRIORITY`, then
        loop `self._task.constraints`, count per `type(c)` and `hdr.update(c.get_fits_headers(n))`.
        If a key is already present (possible only with a subclass of a built-in class next to the
        built-in itself, see Open question 2), keep the first and log once at DEBUG.
- [ ] **Docs** (`docs/source`, no links to `specs/`): a short section "FITS headers of a robotic
      run" in `docs/source/recipes/robotic.rst` after the task YAML example (around line 75),
      listing all `REQ` cards (including `REQ MERIT` once the other plan lands) and the numbering
      rule, and a sentence for plugin authors: override `get_fits_headers(index)` to have a
      constraint written. `Constraint.get_fits_headers` docstring shows up in the API reference.
- [ ] **Changelog**: an entry in `CHANGELOG.md` at release time, as for other changes.

## Tests (no server)

- [ ] `tests/robotic/scheduler/constraints/`: per built-in class, `get_fits_headers(1)` returns
      exactly the expected keys and values; `get_fits_headers(2)` puts the `2` on the type token
      (`HIERARCH REQ SUNALT2 MAX`). `TimeConstraint` gives ISO strings. Base class returns `{}`.
- [ ] Plugin constraint (a `Constraint` subclass defined in the test, not overriding) returns `{}`
      and adds nothing to the mastermind header.
- [ ] **Card length**: for every built-in class, with extreme values (index 9, `max_airmass` 9.9,
      `min_elevation` -90.0, a `TimeConstraint` with full ISO strings) and the comments used, build
      `astropy.io.fits.Card(key, value, comment)` with warnings turned into errors and assert one
      80-char card without truncation (`len(card.image) == 80` and the comment round-trips). Same
      for `REQ PRIORITY` 9999.0 and `REQ PROJECT PRIORITY` 9999.0.
- [ ] `tests/modules/robotic/test_mastermind.py` (pattern of `make_mastermind`, lines 20-40):
  - task with priority, project and constraints of all five types: all cards present;
  - two `SolarElevationConstraint`s and two `TimeConstraint`s: `SUNALT`/`SUNALT2`, `TIME`/`TIME2`;
  - no constraints and priority `None`: only `TASK`/`REQNUM`/... and version cards;
  - no task archive, filesystem-like archive raising `NotImplementedError`, project not found:
    no `REQ PROJECT PRIORITY`, no exception;
  - project priority taken at task start: changing the archive's project afterwards does not
    change the header;
  - `_project_priority` cleared after the task finishes and after it fails.

## Open questions

1. **Write `SUNALT MIN` and `DIR` when they are the defaults (-90, `"both"`)?** Updated
   2026-10-14 after reporter feedback: omit the no-limit bound, retain the direction card.
2. **Count per class or per header token?** Decided per type (class). A subclass of a built-in
   inherits its `get_fits_headers` and would produce the same keys as the built-in in the same task.
   Recommend: keep per class as decided, keep the first card on a clash and log at DEBUG; revisit
   only if a real plugin hits it.
3. **Snapshot project priority at task start or read it per header?** Recommend at task start
   (consistent per run, no work per header).
4. **Round floats?** Recommend no.
5. **Write the cards also for frames taken outside a mastermind run (e.g. `ScriptRunner`)?**
   Recommend no: there is no request there.

## Not verified

- astropy's exact behaviour for a too-long HIERARCH card (raise vs warning vs CONTINUE); the test
  is written to fail in any of those cases.
- Whether the reporter's own planner keeps the constraint list on the task it hands to the
  mastermind (it is their class).
- Whether `LcoTask.project` matches `Project.code` (proposal id) so the project lookup finds it.
- How downstream tools (e.g. pyobs-archive ingestion) treat new HIERARCH keys; not checked.

## Out of scope

- `REQ MERIT` (part 8), see `2026-10-13-fits-header-scheduler-merit.md`.
- Merits (`Task.merits`) as cards; not asked for.
- Changing the measured cards the telescope writes (part 1 of the issue).
