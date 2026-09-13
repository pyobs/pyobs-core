# Per-science-exptime darks on LCO-portal + AstroplanScheduler sites

Status: proposed

Issue: pyobs-core#896

## Problem

`specs/plans/2026-09-01-morning-darks-match-science-exptimes.md` (#831) and
`specs/plans/2026-09-01-per-exptime-dark-masters.md` (#832) built dark masters that match the
previous night's actual science exposure times, via `DarkBiasScript(match_science_exptimes=True)`
(`pyobs/robotic/scripts/calibration/darkbias.py`) deriving the exptime list from the archive at
run time. Both plans were written for the pyobs-portal + `OnDemandScheduler` deployment model —
a `DarkBiasScript` task lives directly in the portal's task archive — and never discussed what the
same feature looks like on an `LcoTaskArchive`/`LcoObservationArchive` + `AstroplanScheduler` site,
where schedulable work is LCO requests, not pyobs-native tasks. #896 asked the question; this plan
answers it in general terms — a concrete per-site instantiation belongs in that site's own repo,
not here (see "Applying this to a site" below).

## What already works, unchanged

- **The reduction half (#832)** — master grouping, per-exptime filenames/cache keys, the
  reference-scale-down calibration policy (ADR 0015) — is archive-level and works on any site,
  LCO-backed or not, as long as per-exptime dark frames with `EXPTIME` set reach the archive.
- **The archive API additions (#831)** (`FrameInfo.exptime`, `list_frames(exptime=...)`) are
  backend-level and apply the same way regardless of scheduler.

So the gap is entirely on the #831 side: how a multi-exptime dark series gets *taken* at all when
the scheduler and task source are LCO's.

## Design: DIRECT-scheduled `SCRIPT` requests, not scheduler-placed ones

The three obstacles #896 originally raised against an LCO-portal site all assumed the dark request
would be *placed by `AstroplanScheduler`* like a normal science block:

1. There's no pyobs task to hang `match_science_exptimes` on — `LcoTaskRunner._get_config_script()`
   (`pyobs/robotic/storage/lco/taskrunner.py:58`) maps a request's `configurations[0].type` to a
   script, and a fixed-exptime `DARK`/`BIAS` type has its exptime baked in at request-creation
   time, long before the night that determines what exptime is actually wanted has happened.
2. pyobs-core can't submit LCO request groups — true for the normal scheduled path
   (`pyobs/robotic/storage/lco/_portal.py` only reads schedulable requests and writes back
   schedule/configuration status).
3. `AstroplanScheduler` plans the whole `start..end` range in one pass
   (`TaskScheduler._create_blocks`) — it doesn't re-evaluate per timestep, so a series whose length
   and exptimes are only known after the fact has no place in that model.

All three stop applying once the request is **DIRECT-scheduled** instead of scheduler-placed: a
request submitted with a concrete `site`/`enclosure`/`telescope`/`start`/`end` (LCO's "direct"
scheduling, as opposed to the normal `requestgroups` + scheduler-placement path) never goes through
`AstroplanScheduler`'s priority placement at all, so point 3 is moot; it can be submitted by
whatever process already has DIRECT-submission access for that site (an external per-site
calibration script, not pyobs-core), so point 2 doesn't need new pyobs-core API surface; and its
exptime doesn't need to be known until the request actually *runs*, because of the dispatch chain
below — so point 1 disappears too.

### The dispatch chain already exists in pyobs-core, fully built

- `LcoTaskRunner._get_config_script()` routes a `SCRIPT`-type config to `LcoScript`
  (`pyobs/robotic/storage/lco/scripts/script.py`).
- `LcoScript` dispatches by the config's `extra_params["script_name"]` to whatever `Script` is
  configured under a site's own `scripts: {name: ...}` map (`LcoTaskRunner`'s `scripts["SCRIPT"]`
  config) — a generic name → script-config mechanism, not something specific to darks.
- `DarkBiasScript` already supports `match_science_exptimes: true` (+ `archive`/`site`), deriving
  the dark series from the archive **when the script runs**, not when the request was created.
  Bias is unaffected (always a fixed `exptime=0` series — there's no science-derived quantity for
  a bias to match).

So a DIRECT-scheduled request of `type: SCRIPT`, `extra_params: {script_name: "<name>"}`, with a
placeholder `exposure_time` (irrelevant — `DarkBiasScript` ignores the request's own instrument
config), dispatches through the existing chain into a `DarkBiasScript(match_science_exptimes=True)`
run exactly like a pyobs-portal deployment's task would. This is not new pyobs-core work; every
piece involved already ships.

### One script entry per binning

`DarkBiasScript` operates at exactly one binning per instance (its own docstring: "exposes at
exactly one binning and never loops over binnings"), so a site running darks at more than one
binning needs one `scripts["SCRIPT"].scripts["<name>"]` entry per binning, each a DIRECT request of
its own.

## Applying this to a site

This plan only establishes that the mechanism exists and how it's shaped; it does not itself wire
up any specific site. A site adopting it needs, in its own config/deployment repo:

- `LcoTaskRunner`'s `scripts["SCRIPT"].scripts` config: one `DarkBiasScript` entry per binning,
  `match_science_exptimes: true`, with that site's `archive`/`site` values.
- Whatever process today submits that site's other DIRECT-scheduled calibration requests (e.g. an
  existing per-site calibration cron) extended to submit the new `SCRIPT`/`<name>` request(s)
  alongside its existing ones, instead of (or in addition to) a fixed-exptime dark request.

See the sibling-repo plan list in `specs/steering/fleet-open-items.md` for concrete per-site
instantiations of this plan as they're written up.

## Open considerations (apply to any site adopting this)

- **Window sizing.** `LcoScript.estimate_duration()` just returns the DIRECT request's own fixed
  `duration` field — it is not recomputed from the exptimes `DarkBiasScript` actually resolves at
  run time. Whatever submits the request has to size its window generously enough up front to fit
  however many distinct science exptimes a real night produces (near-duplicates are
  tolerance-grouped at 1%, `dark_min_exptime` = 5 s, per ADR 0015); there's no way for the request
  itself to self-correct.
- **`Mastermind.allowed_overrun`** — a night resolving to more series than the window was sized for
  runs past the request's end; whether the default (or a per-site override) gives enough slack is
  a per-site operational question, not something this plan can settle in general.
- Not addressing #846 (per-task `archive`/`site` config duplication) — a `match_science_exptimes`
  `DarkBiasScript` entry under `scripts["SCRIPT"].scripts` duplicates `archive`/`site` the same way
  every other `match_science_exptimes` deployment does today.

## Non-goals

- No pyobs-core code changes — everything needed already exists (`LcoTaskRunner`, `LcoScript`,
  `DarkBiasScript`).
- No new LCO request-group submission API in `_portal.py` — DIRECT scheduling uses whatever
  submission path a site's external calibration process already has.
- Bias handling is unchanged — there's nothing for `match_science_exptimes` to buy there.

## References

- pyobs-core#896 (this plan answers it)
- pyobs-core#831/#832, `specs/plans/2026-09-01-morning-darks-match-science-exptimes.md`,
  `specs/plans/2026-09-01-per-exptime-dark-masters.md`, ADR 0015
- `pyobs/robotic/scripts/calibration/darkbias.py`, `pyobs/robotic/storage/lco/scripts/script.py`,
  `pyobs/robotic/storage/lco/taskrunner.py`
