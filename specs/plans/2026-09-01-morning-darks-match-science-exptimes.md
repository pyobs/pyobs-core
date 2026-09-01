# Plan: take morning darks at the night's science exposure times

Status: **proposed**

Tracks issue #831. Robotic/archive half of the dark-exptime-matching work; the reduction half is
`2026-09-01-per-exptime-dark-masters.md` (issue #832), which depends on the archive changes here.
Repos: pyobs-core.

## Problem

`DarkBiasScript` (`pyobs/robotic/scripts/calibration/darkbias.py:25-98`) takes a single series of
darks at one fixed `exptime` (typically 600 s), regardless of what exposure times science frames
actually used that night (chosen per target/filter/binning at runtime by
`ExposureTimeProvider`/`StellarExposureTime`, `pyobs/robotic/utils/exptime/`). Calibration then
linearly rescales that one dark master to whatever the science exptime was
(`_CCDDataCalibrator`, `dark_scale=True` hardcoded) — the noise/error source ADR
`0015-dark-master-strict-exptime-matching-reference-scale-down-only.md` addresses on the
reduction side. This plan makes the *input* to that fix possible: darks taken at the exptimes
that will actually need masters.

The archive API currently carries no exposure-time information at all:

- `FrameInfo` (`pyobs/robotic/utils/archive/archive.py:14-22`) has `id`/`filename`/
  `filter_name`/`binning`/`dateobs` — no `exptime`.
- `Archive.list_frames()`/`list_options()` (same file, `:30-63`) have no `exptime` filter
  parameter, in the abstract base or either implementation.
- `PyobsArchive._build_query()` (`pyobs/robotic/utils/archive/pyobs_archive.py:114-151`) doesn't
  send an `EXPTIME`/exptime query param; `PyobsArchiveFrameInfoDict`/`PyobsArchiveFrameInfo`
  (`:18-38`) don't carry it.
- `LocalArchive._update_root()` (`pyobs/robotic/utils/archive/local_archive.py:34-65`) parses
  FITS headers into a DataFrame but doesn't read `EXPTIME`; `_filter_data()` (`:67-104`) has
  no matching filter branch.

## Design

### 1. Expose exposure time in the archive API

- `FrameInfo`: add `self.exptime: float | None = None` (`archive.py:14-22`).
- `Archive.list_frames()`/`list_options()` (`archive.py:30-63`, abstract): add
  `exptime: float | None = None` parameter to both signatures.
- `PyobsArchive`:
  - `PyobsArchiveFrameInfoDict` (`pyobs_archive.py:18-24`): add `EXPTIME: float`.
  - `PyobsArchiveFrameInfo.__init__` (`:27-38`): set `self.exptime = self.info["EXPTIME"]`.
  - `_build_query()` (`:114-151`): add `exptime` param, send as `params["EXPTIME"] = exptime`
    when not `None` — confirm with pyobs-archive whether it needs an exact-match or
    range-tolerant query param; if the API only supports exact match, do client-side tolerance
    filtering here instead (see #3 below for the tolerance helper this can reuse).
  - `list_options()`/`list_frames()` (`:57-113`): thread `exptime` through to `_build_query()`.
- `LocalArchive`:
  - `_update_root()` (`:34-65`): read `hdr["EXPTIME"]` into a new `exptime` column.
  - `_filter_data()` (`:67-104`): add `exptime: float | None = None` param; when set, filter
    `data["exptime"]` within tolerance (reuse the grouping helper from #2, not a raw `==`, since
    float header values won't compare exactly across frames).
  - `list_options()`/`list_frames()` (`:106-158`): thread `exptime` through; `list_frames()`
    also needs to set `info.exptime = row["exptime"]` when building each `FrameInfo` (`:149-158`
    currently doesn't set `.filename`'s sibling fields exhaustively — check what else is missing
    while touching this).
- `list_options()` return dict (both implementations): add an `exptimes` key alongside
  `instruments`/`binnings`/`filters` — the distinct exposure times present for the queried
  scope. `LocalArchive.list_options()` (`:119-130`) is a straight list-comprehension addition;
  `PyobsArchive.list_options()` (`:57-79`) depends on whether `frames/aggregate/` already
  returns it — check pyobs-archive's endpoint before assuming.

### 2. Helper: distinct science exposure times for a night

New function, `science_exptimes_for_night(archive, site, night, tolerance=0.01,
min_exptime=5.0)` in `pyobs/robotic/utils/calibration.py` (new file — no existing module owns
"derive calibration targets from science data"):

- Lists OBJECT frames (rlevel 0) via `archive.list_frames(night=night, site=site,
  image_type=ImageType.OBJECT, rlevel=0)`, grouped by `(instrument, binning)` — mirrors the
  per-combination looping `Reduction.__call__` already does
  (`pyobs/utils/pipeline/reduction.py:264-297`).
- Drops any frame with `EXPTIME < min_exptime` before grouping — per ADR 0015's
  `dark_min_exptime` (same default, 5 s), calibration treats those as bias-only and never needs a
  dark master, so there's no point scheduling a dark series for them. `min_exptime=0`/`None`
  keeps every exptime, for a caller that wants the full distribution regardless of the ADR's
  default.
- Collapses `exptime` values within `tolerance` (relative, default 1%) into groups, returning
  one representative exptime per group — e.g. round to the group's median or first-seen value.
  This grouping logic is the one both this helper and #832's per-exptime master grouping need;
  consider a small shared utility (`pyobs/utils/exptime_grouping.py` or similar) rather than
  reimplementing the same tolerance-bucketing twice across the two plans.
- Returns `dict[tuple[str, str], list[float]]` keyed by `(instrument, binning)`.
- "Previous night" resolution: accept an explicit `night: str` parameter (matches
  `Archive.list_frames(night=...)`'s existing string format) rather than deriving it from
  `Time.now()` internally — callers (the morning `DarkBiasScript` run) already know what night
  they're running for from their own scheduling context; pushing "what night is 'last night'"
  into this helper would duplicate whatever night-boundary logic the scheduler already has.

### 3. `DarkBiasScript`: multi-exptime support

`pyobs/robotic/scripts/calibration/darkbias.py`:

- Keep `exptime: float = 0` (`:32`) — single-series behavior unchanged, still the default.
- Add `exptimes: list[float] | None = None` (explicit list) and
  `match_science_exptimes: bool = False` (derive via `science_exptimes_for_night`). Validate
  mutual exclusivity with `exptime`/each other in `can_run()` or a pydantic validator — pick
  whichever this repo's other `Script` subclasses already use for cross-field validation
  (check `pyobs/robotic/scripts/` for precedent before adding a new pattern).
- Add optional `archive: dict[str, Any] | Archive | None = None` field, same shape as
  `Reduction`'s (`pyobs/utils/pipeline/reduction.py:27`) — only required when
  `match_science_exptimes=True`; `can_run()` should report "no archive configured" as a
  cannot-run reason rather than raising, consistent with the existing camera-presence check
  (`darkbias.py:41-48`).
- `run()` (`:50-89`): when multiple exptimes are in play, loop series longest-first, calling
  `camera.set_exposure_time()` per series (`:72-73` becomes a per-series call inside the loop);
  `IImageType` stays `dark` for every series (`:74-75`), bias (0 s) stays its own single series
  and is unaffected by this change. Log the resolved exptime list per instrument/binning before
  exposing (`log.info` before the loop) so operators can verify what's about to run without
  waiting for FITS headers.
- `estimate_duration()` (`:91-95`): sum `count * (exptime + readout)` over every series instead
  of the current single-exptime multiplication.

### 4. Docs

Document the new `DarkBiasScript` fields (`exptimes`, `match_science_exptimes`, `archive`) in
`docs/source` wherever morning-calibration task configs are documented today, so this is
discoverable without reading the script source.

## Acceptance criteria

- [ ] `FrameInfo.exptime` populated by both `PyobsArchive` and `LocalArchive`; `list_frames()`/
      `list_options()` accept and honor an `exptime` filter in both implementations.
- [ ] `list_options()` returns an `exptimes` key in both implementations.
- [ ] `science_exptimes_for_night()` returns the distinct, tolerance-grouped science exptimes
      for a site+night, keyed per instrument/binning, excluding exptimes below `min_exptime`
      (default 5 s) unless `min_exptime=0`/`None` is passed.
- [ ] `DarkBiasScript` runs one dark series per exptime (explicit list or
      `match_science_exptimes`-derived) while the single-`exptime` path is unchanged; mutual
      exclusivity between `exptime`/`exptimes`/`match_science_exptimes` is validated, not silently
      resolved by picking one.
- [ ] `estimate_duration()` reflects the multi-series total.
- [ ] Tests: `exptime` filter in both archive implementations (including tolerance behavior),
      `science_exptimes_for_night()` grouping (exact matches, near-duplicates within/outside
      tolerance, empty night, exptimes below/above `min_exptime`), `DarkBiasScript` run/estimate
      with multiple exptimes, mutual-exclusivity validation.

## Out of scope

- Master-dark creation/grouping, exptime matching at calibration time, and the scaling policy —
  `2026-09-01-per-exptime-dark-masters.md` (#832), decided by ADR
  `0015-dark-master-strict-exptime-matching-reference-scale-down-only.md`.
- Flat-field exposure times stay driven by sky brightness (`SkyFlatsScript`/`Scheduler`), not by
  science exposure times — untouched by this plan.
