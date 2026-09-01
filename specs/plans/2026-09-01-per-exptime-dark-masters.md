# Plan: per-exposure-time dark masters, reference-master scale-down only

Status: implemented

Tracks issue #832. Reduction/pipeline half of the dark-exptime-matching work; depends on the
archive `exptime` plumbing from `2026-09-01-morning-darks-match-science-exptimes.md` (#831).
Implements ADR `0015-dark-master-strict-exptime-matching-reference-scale-down-only.md`. Repos:
pyobs-core.

## Problem

Today the reduction pipeline has no concept of dark exposure time:

- `Reduction._create_master_calib()` (`pyobs/utils/pipeline/reduction.py:72-176`), `DARK` branch
  (`:113-127`), combines **all** raw darks of a night into a **single** master per
  instrument/binning via `create_master_dark()` (`pyobs/utils/pipeline/pipeline.py:118-128`).
  The `FILENAME` pattern (`reduction.py:21`) has no exposure-time component, so per-exptime
  masters would collide on the same filename.
- `ReductionBase._master_frames` cache key (`pyobs/utils/pipeline/reduction_base.py:49`) is
  `(ImageType, instrument, binning, filter_name)` — no exptime, so only one dark master per
  instrument/binning can ever be cached.
- `Pipeline.find_master()` (`pyobs/utils/pipeline/pipeline.py:162-217`) matches masters by
  type/instrument/binning/filter and nearest `DATE-OBS` only — never by exptime.
- `_CCDDataCalibrator` (`pyobs/images/processors/calibration/_ccddata_calibrator.py`) always
  passes `dark_scale=True` (`:52`, hardcoded) to `ccdproc.ccd_process`, unconditionally rescaling
  whatever master it was given.

ADR `0015-dark-master-strict-exptime-matching-reference-scale-down-only.md` decides the policy
this plan implements: an exact-exptime-match master is used unscaled; only a configured
reference exptime (default 600 s) may be scaled, and only *down* to shorter science exptimes; an
unmatched science exptime longer than the reference, or with no reference configured, is a
calibration error rather than a silent scale — unless `allow_unmatched_dark_scale=True` opts a
site back into today's always-scale behavior. Science exptimes below a configured minimum
(`dark_min_exptime`, default 5 s) skip dark subtraction entirely and are calibrated with bias
only, ahead of the reference-scale check — dark current is assumed negligible there and an exact
match still wins if one exists.

## Design

### 1. Group raw darks by exposure time when creating masters

`Reduction._create_master_calib()`, `DARK` branch (`reduction.py:113-127`):

- List the night's raw darks with `EXPTIME` included — `self._archive.list_frames(..., image_type=
  ImageType.DARK, ...)` (`:76-83`) already returns `FrameInfo`; once #831 lands, `.exptime` is
  populated on each.
- Group by exptime within a tolerance (reuse the tolerance-grouping helper from #831's plan — see
  that plan's note about sharing it rather than reimplementing; default relative 1%, configurable
  on `Reduction`, e.g. `dark_exptime_tolerance: float = 0.01`).
- Create one master per group via `create_master_dark()` (unchanged, `pipeline.py:118-128`); keep
  the existing `< 3` frames check (`reduction.py:90-93`, `:97-99`) **per group**, logging/skipping
  under-populated groups individually rather than failing the whole night's dark reduction.
- `ReductionBase._master_frames` cache key (`reduction_base.py:49`): extend to
  `(ImageType, instrument, binning, filter_name, exptime | None)` — `exptime` is `None` for
  every non-DARK type (BIAS/SKYFLAT lookups pass `None`, unaffected) and the grouped exptime for
  DARK. `_create_master_calib()`'s cache-store call (`reduction.py:127`) and `_find_master()`
  (`reduction_base.py:82-96`) both need the extra key element threaded through.
- Verify `create_master_dark()`'s underlying `ccdproc.combine()` call
  (`Pipeline._combine_calib_images`, `pipeline.py:41-100`) preserves `EXPTIME` in the combined
  header; `Image.from_ccddata(combined)` (`:91`) carries whatever `combined.header` has. If
  `EXPTIME` doesn't survive combination (sigma-clip/average across frames with the same nominal
  exptime should keep it, but confirm empirically), set it explicitly after combining using the
  group's exptime rather than trusting the header.

### 2. Distinct filenames and progress events for per-exptime masters

- `FILENAME` pattern (`reduction.py:21`): add an exposure-time component, e.g.
  `...-{IMAGETYP}-{EXPTIME|type:exp}-{XBINNING}x{YBINNING}...` — needs a new
  `FilenameFormatter` function (`pyobs/utils/fits.py:91-98`, alongside `_format_type` at `:275-
  292`) that renders `600.0` as `600` (int-like when the value has no fractional part), not a
  literal float-to-string dump. Keep the old pattern available (e.g. as a documented alternate
  `filenames_calib` for deployments that don't want the rename) or call out the filename change
  explicitly in the changelog — existing deployments' archives already contain masters named
  under the old pattern.
- `MasterCalibCreated` (`pyobs/utils/pipeline/progress.py:10-18`): add `exptime: float | None`,
  set from the group's exptime in `_create_master_calib()`'s `_report_progress()` call
  (`reduction.py:165-173`); `None` for BIAS/SKYFLAT, matching the cache-key convention above.
  This is consumed downstream by pyobs-pipeline's progress reporting — flag the field addition to
  that repo when this lands so its consumer doesn't silently ignore it.

### 3. Exposure-time matching + scaling policy at calibration time

Implements ADR 0015's decision directly.

- `Pipeline.find_master()` (`pipeline.py:162-217`): add `exptime: float | None = None` and
  `exptime_tolerance: float = 0.01` params; when `exptime` is given and `image_type ==
  ImageType.DARK`, filter/sort candidates by closeness in exptime, not just `DATE-OBS` (`:210-
  212` currently sorts only by time distance) — an exact-within-tolerance match must win over a
  merely time-close one.
- `Calibration` (`pyobs/images/processors/calibration/calibration.py`):
  - New `__init__` params (`:137-167`): `dark_exptime_tolerance: float = 0.01`,
    `dark_scale_exptime: float | None = 600.0`, `allow_unmatched_dark_scale: bool = False`,
    `dark_min_exptime: float | None = 5.0`.
  - `_find_master_in_archive()` (`:248-269`): for `ImageType.DARK`, read the science image's
    `EXPTIME` from its header and pass it to `Pipeline.find_master()` as the new `exptime` arg.
  - New matching logic (replaces the current "just take whatever dark `find_master` returns")
    per ADR 0015, in order: (1) exact-match (within `dark_exptime_tolerance`) → use unscaled,
    checked first regardless of exptime; (2) no exact match and `dark_min_exptime is not None`
    and science `EXPTIME < dark_min_exptime` (within tolerance) → skip dark subtraction, DARK
    correction omitted from the `ccdproc.ccd_process()` call entirely (bias-only calibration);
    (3) no exact match, `EXPTIME >= dark_min_exptime`, and `dark_scale_exptime is not None` and
    `EXPTIME <= dark_scale_exptime` (within tolerance) → use the reference master (nearest
    available exptime `<= dark_scale_exptime` in the archive) scaled down; (4) else if
    `allow_unmatched_dark_scale` → fall back to today's behavior (whatever `find_master` returns,
    scaled, regardless of direction); (5) else → raise `ValueError` listing the requested exptime
    and the available master exptimes. This is caught by the existing `except ValueError` in
    `__call__` (`:179-183`), which already logs a warning and returns the image uncalibrated —
    no new exception-handling path needed there.
  - `_CCDDataCalibrator` (`_ccddata_calibrator.py`): change `dark_scale=True` (`:52`) to a
    constructor parameter, `dark_scale: bool = True` on `__init__` (`:10`), threaded from
    `Calibration.__call__` (`:185-186`) based on which matching branch fired above. Only pass
    `dark_exposure=self._dark_exp_time * u.second` (`:50`) when `dark_scale` is actually `True`
    — an unscaled exact-match dark shouldn't carry a spurious `dark_exposure` into
    `ccd_process()`. For the bias-only branch (2), `Calibration` needs a way to invoke
    `_CCDDataCalibrator` (or the underlying `ccd_process()` call) with no dark master at all —
    check whether that means a new `dark_frame: CCDData | None = None`-accepting path on
    `_CCDDataCalibrator.__init__` (`:10`) or a separate bias-only calibrator branch in
    `Calibration.__call__`; either way, bias subtraction itself must still run unchanged.

### 4. Reduction integration

- `ReductionBase._find_master()` (`reduction_base.py:59-96`): add `exptime: float | None = None`
  param, threaded to `self._pipeline.find_master(...)` (`:87-89`) and used as part of the cache
  key (see #1).
- `Reduction._calib_data()` (`reduction.py:198-244`): no direct change needed —
  `self._pipeline.calibrate(image)` (`:215`) already runs the `Calibration` processor, which now
  reads `EXPTIME` from the science image's own header (`calibration.py`, per #3) rather than
  needing it passed explicitly from `Reduction`.

## Open questions -- resolved during implementation

- `dark_exptime_tolerance` is relative-only (matching #831's `exptimes_close`/`group_exptimes`,
  which this plan already reuses). No absolute-tolerance mode was added -- not needed for the
  discrete, well-separated exptimes real detectors use, and would have doubled the parameter
  surface across `Reduction`, `Pipeline.find_master`, and `Calibration` for no concrete use case.
- Filename-pattern migration: hard rename, called out here and in the PR description rather than
  adding a second configurable pattern. Existing archives keep their old-pattern masters under
  their original filenames; only newly-created masters (BIAS/SKYFLAT included, since the pattern
  is shared) use the new `{EXPTIME|exptime}` component.

## Acceptance criteria

- [x] A night with darks at multiple exposure times produces one distinct master dark per
      exposure time — distinct filenames, cache entries, and `MasterCalibCreated` events each
      carrying the correct `exptime`.
- [x] Science frames are calibrated with the exptime-matching master (within tolerance),
      unscaled, whenever one exists.
- [x] Scaling happens only via the reference master, only downward (science `EXPTIME <=
      dark_scale_exptime`); a science frame with no matching master and `EXPTIME >
      dark_scale_exptime` fails calibration with a clear, catchable error instead of silently
      scaling.
- [x] `allow_unmatched_dark_scale=True` reproduces today's always-scale behavior exactly, for
      sites not yet taking per-exptime darks.
- [x] A science frame with `EXPTIME < dark_min_exptime` and no exact-match dark master is
      calibrated with bias only (no dark correction applied, no error); an exact-match master for
      that exptime, if one exists, is still used ahead of the bias-only path.
- [x] Backward compatibility: existing `Calibration` *configs* keep validating and running
      unchanged (all new `__init__` params default to today's ADR-0015-approved policy) -- but
      per ADR 0015's own "Consequences", *behavior* changes for a site relying on
      always-scale-whatever's-nearest: it now fails calibration (a caught `ValueError`, not a
      crash) for science exptimes outside its one master's tolerance, until it sets
      `allow_unmatched_dark_scale=True` or takes per-exptime darks (#831). Documented in
      `CHANGELOG.rst` (not just here) per the ADR's explicit requirement. The filename-pattern
      change is a separate, also-documented migration step.
- [x] Tests: master grouping by exptime (incl. tolerance, under-populated groups skipped
      individually); filename/cache-key/progress-event exptime plumbing; matching logic
      (exact match / bias-only-below-minimum / reference-scale-down / reference-scale-up rejected
      / unmatched-strict-error / `allow_unmatched_dark_scale` fallback); `_CCDDataCalibrator`'s
      `dark_scale` parameter behavior in both states; `dark_min_exptime=0`/`None` disables the
      bias-only branch.

## Out of scope

- Taking darks at multiple exptimes in the first place, and exposing `exptime` on the archive
  API — `2026-09-01-morning-darks-match-science-exptimes.md` (#831), a prerequisite for this
  plan's grouping step (#1) to have real per-exptime data to group.
