# Plan: Harden and rename `Night` → `Reduction`; complete `LocalArchive` I/O

Status: implemented. All code and test items landed via PR #743 (2026-08-09) on `develop`, plus a
follow-up (`dd014f70`) that added structured progress reporting and split out `ReductionBase`.
Open item: the three site YAML configs (outside this repo) still need the deploy-time
`Night`→`Reduction` dotted-path update.

Related: `specs/plans/pyobs-pipeline.md` (issue #741) — blocking prerequisite. The pipeline-web
project's `SitePipeline` model assumes input and output can each independently be a local
directory or a `PyobsArchive`; `Night` and `LocalArchive` don't support that combination today.
This plan should land (or at least be decided) before pipeline-web's Celery task (its Step 5) is
implemented against them.

## Problem

Reviewing `pyobs/utils/pipeline/night.py` and `pyobs/robotic/utils/archive/local_archive.py` while
designing pipeline-web surfaced one blocking gap and several correctness bugs:

### Blocking: `Night` can't have a different input and output archive

`Night.__init__(self, archive, pipeline, ..., store_local=None, ...)` takes exactly one `archive`
object. It's used for both reading raw and calibration frames (`list_frames`/`download_frames`)
*and*, when `store_local` is unset, for writing results back (`upload_frames`). `store_local` only
redirects output to a local directory — there's no way to say "read from archive A, write to
archive B" or "read from a local directory, write to a remote archive." Every write path either
goes to the same object frames were read from, or to a local path.

pipeline-web's plan has `SitePipeline.input_type`/`output_type` chosen independently between
`local` and `archive`. Two of the four combinations (`local`→`archive`, `archive A`→`archive B`)
aren't expressible against `Night` as it stands.

### Bug: `LocalArchive.upload_frames` silently discards data

```python
# pyobs/robotic/utils/archive/local_archive.py:168
async def upload_frames(self, images: list[Image]) -> None:
    pass
```

The `Archive` base class's default `upload_frames` raises `NotImplementedError` — `LocalArchive`
deliberately overrides that with a silent no-op (confirmed intentional: there's an existing test,
`test_upload_frames_is_noop`, asserting exactly this). But for pipeline-web's `local` output type,
this is the actual write path. Today, a `Night` run configured with a `LocalArchive` as its
archive and no `store_local` override computes every calibrated frame, logs "Uploading...", and
throws the result away — no exception, no warning, nothing in the FITS files on disk.

### Other bugs found in `Night`

1. **One bad calib frame aborts the whole run.** `_calib_data` (per-science-frame loop) wraps each
   frame in try/except so a single bad frame doesn't abort the night. `_create_master_calib` and
   its callers in `__call__` have no exception handling at all — a network hiccup or corrupt FITS
   while building one instrument's flat field propagates out of `__call__` entirely, aborting every
   remaining instrument/binning/filter combination too.
2. **Inconsistent post-download frame-count check.** Before download: `if len(infos) < 3: return
   None` bails cleanly. After download: `if len(images) < 3: log.warning(...)` — no `return None`.
   A partial download failure logs a warning and falls through into
   `create_master_bias/dark/flat` with too few (possibly zero) images.
3. **No directory creation for `store_local`.** `calib.writeto(os.path.join(self._store_local,
   ...))` with no `os.makedirs(self._store_local, exist_ok=True)` first. A freshly-configured,
   not-yet-created local output path throws `FileNotFoundError` on first run.
4. **`store_local` docstring is wrong.** Says "If True, files are stored..." — it's a directory
   path (`str | None`), not a bool.
5. **`worker_procs` does nothing.** Documented as "number of worker processes," stored in
   `self._worker_processes`, never read anywhere else in the file. `__call__` is a plain
   sequential `await` loop with no concurrency.

### Naming: `Night` doesn't fit solar telescopes

Same reasoning that drove pipeline-web's `ObservationPeriod` → `ReductionPeriod` rename: `Night`
reduces one calendar period's frames regardless of whether the telescope observes at night or
during the day, so the name is misleading for solar sites. Since this plan is already changing
`Night.__init__`'s signature, it's the natural point to rename the class too, rather than
stabilizing the old name and having to touch every caller again later.

## Non-goals

- **Systemic `**kwargs: Any` typo-swallowing across `Object`-derived classes.** `Reduction` itself
  doesn't inherit from `Object` and has no `super().__init__()` call, so its `**kwargs: Any` is a
  pure, local dead end — trivial to remove (item 5 below). Most other pyobs-core classes *do*
  inherit from `Object` (`pyobs/object.py:239`), whose own `__init__` is the actual terminal sink
  for framework kwargs (`vfs`, `comm`, `timezone`, `location`, `observer`) and silently drops
  anything left over. Fixing that choke point is a separate, much larger change (touches every
  config-driven class in the codebase, and needs deciding warn-vs-raise against real configs first)
  — tracked in `specs/plans/object-kwarg-validation.md`, out of scope here.
- **Live log/progress streaming for pipeline-web's log viewer.** No `Night` change is needed for
  this — standard `logging.Handler` attachment in the Celery task (pipeline-web's own code) is
  sufficient, since `Night` already logs through the normal `logging` module. Belongs in the
  pipeline-web plan, not here.
- **Implementing real parallelism for `worker_procs`.** Actually using the parameter (e.g.
  `asyncio.Semaphore`-gated `asyncio.gather` across instrument/binning/filter combinations) is a
  reasonable follow-up but not required to unblock pipeline-web, and changes concurrency behavior
  in a way that deserves its own review. This plan only removes the misleading unused parameter;
  re-adding real concurrency is a separate future plan if wanted.

## Decision

### 1. Separate input and output on `Night`, unified as a single `output` parameter

Decision: replace `store_local` with a single `output` parameter, type-discriminated — a string is
a local directory path, a dict/`Archive` is an output archive. This unifies the "where do results
go" concept into one parameter instead of two (`store_local` + a separately-added
`output_archive`), which is the cleaner long-term shape. It's a breaking rename of `store_local`,
but a free one: none of the three current site configs set `store_local` at all (checked — they
only configure `archive`), so there's no live config to migrate beyond the `Night`→`Reduction`
dotted-path update already required by item 3 below.

**File:** `pyobs/utils/pipeline/night.py` (see item 3 below — renamed to `reduction.py`/`Reduction`
as part of this same plan; shown here under the new name directly rather than as an interim step)

```python
class Reduction:
    def __init__(
        self,
        archive: dict[str, Any] | Archive,
        pipeline: dict[str, Any] | Pipeline,
        filenames_calib: str = FILENAME,
        min_flats: int = 10,
        output: str | dict[str, Any] | Archive | None = None,
        create_calibs: bool = True,
        calib_science: bool = True,
    ):
        """...
        Args:
            archive: Archive to fetch raw and calibration frames from. Also the output
                destination, unless output is set.
            output: Where to write results. A string is a local directory path; a dict or
                Archive is an output archive. If not set, results are written back to archive.
        """
        self._archive = get_object(archive, Archive)
        self._store_local: str | None = output if isinstance(output, str) else None
        self._output_archive = (
            self._archive if output is None or isinstance(output, str) else get_object(output, Archive)
        )
        ...
```

Replace both `self._archive.upload_frames(...)` call sites (`_create_master_calib`,
`_calib_data`) with `self._output_archive.upload_frames(...)` — used only when `self._store_local`
is falsy, same precedence local-over-archive logic that already exists. Reads (`list_frames`,
`download_frames`, `list_options`) stay on `self._archive` — unchanged.

This makes all four of pipeline-web's `input_type`/`output_type` combinations expressible:

| input_type | output_type | Reduction config |
|---|---|---|
| archive | archive (same) | `archive: {...}` only (today's default path, unchanged) |
| archive | archive (different) | `archive: {...}`, `output: {...archive config...}` |
| archive | local | `archive: {...}`, `output: <path>` |
| local | archive | `archive: {class: LocalArchive, root: <path>}`, `output: {...archive config...}` |
| local | local (same or different dir) | `archive: {class: LocalArchive, root: <in>}`, `output: <out path>` |

### 2. Implement `LocalArchive.upload_frames`

**File:** `pyobs/robotic/utils/archive/local_archive.py`

```python
async def upload_frames(self, images: list[Image]) -> None:
    self._root_path.mkdir(parents=True, exist_ok=True)
    for image in images:
        filename = image.header.get("FNAME")
        if not filename:
            raise ValueError("Image has no FNAME header set, cannot determine output filename.")
        image.writeto(str(self._root_path / filename), overwrite=True)
    self._update_root()  # refresh the in-memory index so newly-written frames are queryable
```

Calling `_update_root()` after writing matters: a `LocalArchive` used as both a night's `archive`
(for the *next* night's calibration frame lookups) and its `output` archive needs freshly uploaded
master calibs to show up in subsequent `list_frames`/`_find_master` calls in the same process, not
just on the next `model_post_init`.

A missing `FNAME` header raises `ValueError` — this is a caller error (image wasn't formatted
before upload), not an unimplemented-feature situation, so `ValueError` reads more clearly than
falling through to the `Archive` base class's `NotImplementedError` default.

The existing `test_upload_frames_is_noop` test asserts the current no-op behavior and needs
replacing (not just leaving alongside the new behavior).

### 3. Rename `Night` → `Reduction`

**Files:**
- `pyobs/utils/pipeline/night.py` → `pyobs/utils/pipeline/reduction.py`, `class Night` →
  `class Reduction`, docstring "Creates a Night object for reducing a given night" → "Creates a
  Reduction object for reducing a given observation period."
- `pyobs/utils/pipeline/__init__.py`: `from .night import Night` → `from .reduction import
  Reduction`; `__all__ = ["Night", "Pipeline"]` → `__all__ = ["Reduction", "Pipeline"]`

No other file in pyobs-core imports `Night` (checked — only `pipeline/__init__.py` does; other
hits for the word "night" elsewhere in the codebase are unrelated prose/variable names, not this
class). No test file exists for it today, so nothing to update there.

**No backward-compatible alias.** Every existing YAML config with `class:
pyobs.utils.pipeline.Night` breaks (`get_class_from_string` fails to import the old dotted path)
until updated to `pyobs.utils.pipeline.Reduction`. This includes the three site configs the
current (non-web) pipeline runs against — those need updating by hand at deploy time, outside this
repo. Flagging explicitly since it's a manual, easy-to-forget step, not something this plan's
checklist can cover.

### 4. Fix the remaining `Reduction` bugs found alongside

**File:** `pyobs/utils/pipeline/reduction.py` (post-rename path)

- Wrap the calibration-frame creation calls in `__call__` (the `_create_master_calib` calls for
  BIAS/DARK/SKYFLAT) in try/except per instrument/binning/filter combination, logging and
  continuing rather than propagating — matching the fault-tolerance `_calib_data` already has for
  science frames.
- Add `return None` after the post-download `len(images) < 3` warning in `_create_master_calib`,
  matching the pre-download check's behavior.
- `os.makedirs(self._store_local, exist_ok=True)` once in `__init__` when `output` resolves to a
  local path (or lazily before the first write — either is fine, `__init__` is simpler).
- The old `store_local` docstring bug (said "If True, ..." for what was actually a path) is moot
  once `output` replaces it — just make sure the new `output` docstring is accurate from the start.
- Remove `worker_procs` and `self._worker_processes` — it's dead, and keeping an unused parameter
  that implies concurrency is worse than not having it.

### 5. Remove `Reduction.__init__`'s dead `**kwargs: Any`

`Reduction` (formerly `Night`) doesn't inherit from `Object` and never calls a `super().__init__()`
— unlike most pyobs-core classes, its `**kwargs: Any` isn't threading shared framework parameters
anywhere, it's a pure sink that silently discards anything not matching a named parameter. Simply
deleting it from the signature means Python's own keyword-argument matching does the validation
for free: an unexpected kwarg becomes `TypeError: unexpected keyword argument`, not silent nothing.

This does mean any config currently passing `worker_procs` (dead since item 4 above removes it
too) will now raise instead of silently no-op. That's the point — it surfaces exactly the kind of
stale/typo'd config this whole item exists to catch, and none of the three current site configs
set `worker_procs`, so nothing live actually breaks.

The broader systemic version of this fix — `Object.__init__` itself, which *does* need to keep
absorbing kwargs for the subclass-chain-threading reason — is out of scope here; see Non-goals and
`specs/plans/object-kwarg-validation.md`.

## Open questions

(none — the `**kwargs` question is now split: `Reduction`'s own case is fixed by item 5 above, the
systemic `Object.__init__` case has its own plan, `specs/plans/object-kwarg-validation.md`.)

## Implementation checklist

- [x] Rename `pyobs/utils/pipeline/night.py` → `reduction.py`, `class Night` → `class Reduction`
- [x] Update `pyobs/utils/pipeline/__init__.py` import and `__all__` for the rename
- [x] `Reduction.__init__`: replace `store_local` with unified `output: str | dict | Archive |
      None` parameter, type-discriminated (str → local path, dict/Archive → output archive, None →
      defaults to `archive`)
- [x] `Reduction`: route `_create_master_calib` and `_calib_data` uploads through
      `self._output_archive` (local-path case still handled by `self._store_local`, same
      precedence as before)
- [x] `Reduction`: wrap calibration-frame creation in `__call__` in per-combination try/except
- [x] `Reduction`: fix post-download frame-count check to `return None`
- [x] `Reduction`: create the local output directory if missing, when `output` resolves to a path
- [x] `Reduction`: remove unused `worker_procs`/`self._worker_processes`
- [x] `Reduction.__init__`: remove dead `**kwargs: Any` so unexpected/typo'd config keys raise
      `TypeError` instead of being silently discarded
- [x] `LocalArchive.upload_frames`: implement real write (root-relative `FNAME`, raising
      `ValueError` if missing, `mkdir`, `_update_root()` refresh)
- [x] Update/replace `test_upload_frames_is_noop` to assert real write behavior
- [x] New tests: `Reduction` with `output` set to an archive (input and output land in different
      archives) and to a local path, per-combination exception isolation in calibration creation,
      local output directory auto-creation, `LocalArchive.upload_frames` writing + re-listability
      via `_update_root()`, `LocalArchive.upload_frames` raising `ValueError` on missing `FNAME`,
      `Reduction(**{"typo_kwarg": 1}, ...)` raising `TypeError`
- [ ] Manually update the three site YAML configs (outside this repo) from `class:
      pyobs.utils.pipeline.Night` to `pyobs.utils.pipeline.Reduction` at deploy time — none of them
      currently set `store_local`, so no `output`-shape migration needed beyond the class rename
- [x] Update this doc's `Status:` to `implemented` once landed
- [x] Un-block `specs/plans/pyobs-pipeline.md` Step 5 (Celery task) — update its `Night` reference
      to `Reduction`, and its config-building pseudocode should be revisited to build the unified
      `output` parameter (archive dict or local path string) for the `local`→`archive` and
      `archive`→`archive` (different) cases
