# Dark masters: strict per-exposure-time matching, reference master scales down only

status: accepted
date: 2026-09-01

## Context and Problem Statement

`Calibration`/`_CCDDataCalibrator` (`pyobs/images/processors/calibration/_ccddata_calibrator.py:52`)
always linearly rescales whatever master dark it found to the science frame's exposure time
(`dark_scale=True` hardcoded, `ccdproc.ccd_process`). `Reduction._create_master_calib`
(`pyobs/utils/pipeline/reduction.py:113-127`) combines **all** of a night's raw darks into a
single master per instrument/binning, with no notion of exposure time at all — so today there is
exactly one dark master to scale from, regardless of how far the science exptime is from it.

Linear dark scaling is only valid in a detector's linear dark-current regime; for long exposures
or non-linear detectors it's a known source of extra noise/error (issue #832). #831 (robotic
side, tracked separately) makes it possible to take darks at the actual science exposure times
used during the night instead of one fixed value. This ADR is the policy decision #832 flags as
needing one before the reduction-side implementation can proceed: once per-exposure-time masters
exist, when is scaling still allowed, and what happens when nothing matches?

Three sub-questions, decided together because they define the same "escape hatch":

1. **Default behavior for `dark_scale_exptime`** (`Calibration`'s new option) — does an
   unmatched science exptime keep today's silent always-scale behavior by default, or fail
   loudly unless it matches a master exactly or matches the configured reference exptime?
2. **Scale direction for the reference master** — if a 600 s reference master is kept for
   scaling, can it scale to *any* other exptime (both up and down), or only one direction?
3. **Minimum exptime to apply a dark at all** — very short science exposures (a few seconds)
   see negligible dark current; is there an exptime below which dark subtraction is skipped
   entirely rather than matched or scaled?

## Considered Options

### Default behavior

* **Preserve current always-scale behavior by default** (`allow_unmatched_dark_scale=True`
  out of the box) — zero risk of breaking an existing deployment's calibration on upgrade; sites
  opt into strict matching only once they've taken per-exptime darks for their exposure times.
* **Strict by default** (`dark_scale_exptime=600.0`, `allow_unmatched_dark_scale=False`) — an
  exact-match master is used unscaled; the 600 s reference master may only scale in one direction
  (see below); anything else is a calibration error, not a silent scale.

### Scale direction

* **Bidirectional** — the reference master scales to any science exptime, shorter or longer.
* **Reference → shorter only** — the reference master (600 s) only scales *down* to science
  frames with `EXPTIME < 600 s` (within tolerance). A science frame requesting `EXPTIME > 600 s`
  with no exact-match master fails calibration instead of scaling the reference up.

### Minimum exptime for dark subtraction

* **No minimum** — every science frame goes through the matching/scaling logic above,
  regardless of how short its exptime is; a 2 s frame with no exact-match master either scales
  the reference down to 2 s or fails, same as any other exptime.
* **Configurable minimum, bias-only below it** (`dark_min_exptime: float = 5.0`) — a science
  frame with `EXPTIME < dark_min_exptime` and no exact-match dark master skips dark subtraction
  entirely and is calibrated with bias only; an exact-match master, if one happens to exist for
  that exptime, is still used ahead of this check (exact match always wins).

## Decision Outcome

Chosen: **strict by default, reference-master scaling in one direction only (down), with a
configurable minimum exptime below which dark subtraction is skipped**.

- `Calibration` ships with `dark_scale_exptime: float | None = 600.0` and
  `allow_unmatched_dark_scale: bool = False`. A science frame is calibrated with an exact-match
  dark master (within `dark_exptime_tolerance`, default relative 1%) unscaled whenever one
  exists. Failing that, if its `EXPTIME` is `<= dark_scale_exptime` (within tolerance), the
  reference master is used scaled down (`dark_scale=True`, `dark_exposure=dark_scale_exptime`).
  Anything else — no exact match, and `EXPTIME > dark_scale_exptime` — is a calibration error
  listing the requested exptime and the available master exptimes; `Calibration.__call__`
  already logs a warning and returns the uncalibrated image on this path (`calibration.py:180-183`),
  so a science frame is never silently discarded, only left uncalibrated with a clear log entry.
  Setting `dark_scale_exptime=None` disables the reference-scale fallback entirely (exact match
  or nothing); `allow_unmatched_dark_scale=True` is the explicit opt-out back to today's
  always-scale-whatever-you-found behavior, for a site that hasn't taken per-exptime darks yet.
- `Calibration` also ships `dark_min_exptime: float = 5.0`. The full matching order for a DARK
  correction is: (1) exact-match master (within `dark_exptime_tolerance`) → unscaled, always
  checked first regardless of exptime; (2) no exact match and science `EXPTIME <
  dark_min_exptime` → skip dark subtraction, calibrate with bias only; (3) no exact match,
  `EXPTIME >= dark_min_exptime`, and `EXPTIME <= dark_scale_exptime` → reference master scaled
  down; (4) `allow_unmatched_dark_scale=True` → legacy always-scale fallback; (5) otherwise →
  calibration error. Setting `dark_min_exptime=0` (or `None`) disables the bias-only step,
  restoring the exact/reference/error flow this ADR otherwise decides. The default of 5 s is a
  starting point, not a measured cutoff for any specific detector — sites with detectors that
  show dark current at low exptimes should lower it or set it to 0.
- This is a deliberate breaking change in default behavior. It is the entire point of #832 — a
  default that keeps silently scaling is a default that keeps the noise/error problem live. The
  "preserve current behavior by default" option would ship a strict-matching *capability* nobody
  uses until they remember to flip a flag, which defeats the reason the issue was filed. The
  breaking-change cost is bounded and known: rollout means checking each site's `Calibration`
  config after upgrading (MONET, iag50, and others tracked via [[project_blocking_sdk_survey]]-
  style survey) and either confirming per-exptime darks are being taken (#831) or setting
  `allow_unmatched_dark_scale=True` explicitly until they are.
- Reference scaling only shrinks the exposure time it's applied to (down), never grows it.
  Scaling a dark *up* amplifies whatever read-noise and fixed-pattern-noise contribution it
  carries proportionally more than scaling it down does — the reference master is deliberately
  the *longest* well-behaved dark a site takes, precisely so scaling from it is always a
  reduction. Allowing the reverse (grow a 600 s dark to cover a hypothetical 900 s science frame)
  would reintroduce the same "scaling amplifies the wrong way" risk the issue exists to close off,
  for a case that in practice doesn't come up: science exptimes at the sites this repo serves run
  shorter than the reference, not longer. If a site's usage pattern is different (longer science
  exptimes than 600 s becomes common), the fix is to raise `dark_scale_exptime` to that site's own
  longest well-sampled dark, not to allow upward scaling from a shorter one.

### Consequences

* Good, because calibration output stops silently degrading for exposure times far from
  whatever one master happened to exist — either it's matched properly or the failure is visible
  in logs immediately, not as noise nobody traced back to dark scaling.
* Good, because the direction restriction matches the physical justification (scaling down is
  the safe direction) rather than leaving both directions open "because the code already supports
  it" — `dark_exposure`/`data_exposure` in `ccdproc.ccd_process` don't distinguish direction
  themselves, so this has to be enforced explicitly in `Calibration._find_master`/matching logic,
  not assumed from the library.
* Bad, because every site's `Calibration` config needs a rollout check on upgrade — a site that
  takes darks at only one exptime and relies on scaling for everything else will start failing
  calibration for out-of-tolerance science frames until it either sets
  `allow_unmatched_dark_scale=True` or adopts #831's multi-exptime darks. This must be called out
  in the changelog, not discovered from a support ticket.
* Neutral, because `dark_exptime_tolerance` and `dark_scale_exptime` are both configurable —
  a site with a stable, well-characterized detector can widen the tolerance or raise the
  reference exptime to reduce how often it hits the strict-failure path, without needing another
  code change.
* Bad, because a science exptime longer than `dark_scale_exptime` with no exact-match master has
  no fallback at all under this decision — it fails, full stop, rather than scaling up as a
  degraded-but-better-than-nothing option. Accepted as the safer failure mode; revisit only if a
  real site's exptime distribution runs longer than its reference dark and per-exptime darks
  aren't a viable fix for it.
* Good, because `dark_min_exptime` means short science exposures no longer need a per-exptime
  dark master (#831) taken at all, or hit the reference-scale-down path with a very small
  divisor — bias-only calibration avoids both the wasted calibration-time cost of taking darks
  nobody needs and the noise amplification of scaling a 600 s dark down to a couple of seconds.
* Neutral, because 5 s is an unvalidated default; a site whose detector shows measurable dark
  current below 5 s needs to lower `dark_min_exptime` (or set it to 0) rather than relying on the
  out-of-the-box value being correct for its hardware.
