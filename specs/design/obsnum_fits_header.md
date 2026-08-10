# `OBSNUM`: per-night observation counter in FITS headers

Status: implemented, closed. Tracks #738. Repos: pyobs-core, pyobs-robotic-backend.
Landed in pyobs-core#746 (released 2.0.0.dev71) and pyobs-robotic-backend#69.

## Problem

Issue #738, as filed: no stable, sequential identifier links FITS files back to the observation
that produced them. `OBJECT` (target name) is the only observation-relevant keyword currently
written. `FRAMENUM` (`pyobs/mixins/fitsheader.py:186-235`) is a per-camera, per-night frame counter
with no awareness of observations — finding all frames for one observation means matching on target
name + time window, which breaks when the same target is observed twice in a night.

`Observation.id` (`pyobs/robotic/observation.py:31`) exists but isn't a fit for this: it's set
inconsistently (UUID in `ObservationArchiveEvolution` (`observationarchiveevolution.py:47`), unset
in `AstroplanScheduler`, `LcoScheduleReader`, `MockLcoObservationArchive`, ...), and where it *is*
set it's a UUID — not the short, human-readable, per-night sequence number the issue asks for.

## Where the pieces actually are

Traced who holds what, since the issue's own "where it fits" pointers (`FitsHeaderMixin`,
`ObservationArchive`) turned out not to be where the relevant state lives:

- **`Mastermind`** (`pyobs/modules/robotic/mastermind.py`) is the only module that ever holds the
  `Observation` object. Its run loop (`_run_thread`, `mastermind.py:154`) pulls one off the
  `ObservationArchive`, then immediately discards everything except `self._task = observation.task`
  and `self._task_target = observation.target` — the `Observation` itself (start/end/state/id) isn't
  kept.
- `Mastermind` already implements `IFitsHeaderBefore` and contributes headers per running task via
  `get_fits_header_before()` (`mastermind.py:203-222`): `TASK` (task name) and **`REQNUM`
  (`str(self._task.id)`)**. This already answers one of the issue's open questions — "also include
  `task.id` as a separate header (`TASKID`)?" — `REQNUM` already is that header, just under a
  different name. No new keyword needed there.
- **`FitsHeaderMixin`** (`pyobs/mixins/fitsheader.py`) lives on the *camera* module, not anywhere
  observation-aware. It has no concept of "observation" at all — it only tracks `FRAMENUM`, a
  counter local to that one camera module instance, persisted via `module.vfs.read_yaml`/
  `write_yaml` to `/pyobs/modules/{module.name}/cache.yaml`, reset when `DAY-OBS` changes
  (`_fitsheadermixin_add_framenum`, `fitsheader.py:206-235`). Multiple cameras each run their own
  `FitsHeaderMixin` instance with independent state.
- **`ObservationArchive`** (`pyobs/robotic/storage/observationarchive.py`) is an abstract interface
  with four+ implementations (`memory`, `filesystem`/YAML, `backend`, `lco`). `lco` in particular
  proxies an external system (LCO's portal API) that has its own request numbering — adding a
  counter *inside* the archive means reimplementing it four times, once against an external API that
  doesn't expose a compatible counter at all.
- Both `Mastermind` and `FitsHeaderMixin` are `Object`s (`pyobs/object.py`) and so both can be
  configured with `observer:`/`location:` independently (see
  `specs/design/module_observer_location.md`) — `Mastermind` computing its own `DAY-OBS`-equivalent
  night boundary via `Time.now().night_obs(self._observer)` needs no new plumbing.

## Why this determines the design, not just where to put a function

The issue's two open questions — "per-module or global snapshot" (framed for #739, but the same
question applies here) and "counter location: `FitsHeaderMixin` or `ObservationArchive`?" — have a
answer forced by what the header is *for*: `OBSNUM` is supposed to be one stable number that
identifies *the observation*, shared by every frame taken during it. A facility can point more than
one camera/instrument at the same target during one observation (e.g. simultaneous imager +
spectrograph). If each camera's `FitsHeaderMixin` kept its own counter (mirroring `FRAMENUM`), two
cameras imaging the same observation would get two different `OBSNUM` values — which defeats the
stated purpose ("night + OBSNUM uniquely identifies an observation").

`Mastermind` is the only place a single counter value can be shared across every camera that
receives headers for that observation, because it's the only place already broadcasting headers
*for the observation* (not per-camera) via `get_fits_header_before()`, over the same
`IFitsHeaderBefore` RPC that already fans out `TASK`/`REQNUM` to every requesting client
(`FitsHeaderMixin.request_fits_headers`, `fitsheader.py:60-91`). No new RPC path is needed — `OBSNUM`
rides the existing one.

## Proposed design

**Counter owner**: `Mastermind`, incremented once per observation (at task start,
`mastermind.py:154`, not per frame) — not `FitsHeaderMixin`, not `ObservationArchive`.

**Persistence**: reuse `FitsHeaderMixin`'s existing pattern rather than inventing a new one — a VFS
cache file (e.g. `/pyobs/modules/{module.name}/obsnum.yaml`) holding `{night, obsnum}`, read/written
via `module.vfs.read_yaml`/`write_yaml`, reset to 1 when the computed night differs from the cached
one. This is the same shape of state `FRAMENUM` already persists, just keyed to observations instead
of frames.

**Scope decision: write the counter fresh for `Mastermind`, don't touch `FitsHeaderMixin`/`FRAMENUM`.**
`_fitsheadermixin_add_framenum` (`fitsheader.py:186-235`) and the new `Mastermind` counter are the
same algorithm underneath ("load `{night, n}` from a VFS cache, bump `n` if night matches, reset to 1
if it doesn't, write back"), and a shared `NightlyCounter` helper was considered — but decided
against for this PR: extracting it means rewriting `FitsHeaderMixin`'s existing, working
`FRAMENUM` logic (including its increment-before-cache-check quirk, see "Still open") as a side
effect of an unrelated feature, and a regression there would hit every camera module, not just
`Mastermind`. `Mastermind`'s counter is implemented standalone (own small increment/reset/persist
block, not shared code) — some duplication with `FRAMENUM`'s pattern remains, revisit only if a
third counter shows up and the duplication actually starts costing something.

**New header**: `OBSNUM`, the same compound string as `Observation.obsnum` (see below), written by
`Mastermind.get_fits_header_before()` alongside the existing `TASK`/`REQNUM`:

```python
hdr["OBSNUM"] = FitsHeaderEntry(self._obsnum, "Observation number (night-obsnum)")
```

One representation, not two — `self._obsnum` is the compound string itself
(`f"{night:%Y%m%d}-{counter:03d}"`, e.g. `"20260810-001"`), used verbatim both as the FITS keyword
value and as `Observation.obsnum`. (An earlier version of this doc split it — bare int in FITS
paired with `DAY-OBS`, compound string only on the model — but there's no reason to maintain two
representations of the same value; the compound form is self-contained in both places and DAY-OBS
stays available in the header regardless, so nothing is lost by writing the full string.)

`{counter:03d}` (3 digits, rolling over at 1000/night) was checked against realistic
observations-per-night and kept as-is — not widened. Note this is *observations* per night, not
*frames*; 3 digits is comfortable headroom for that even on short-cadence nights.

`self._obsnum` is computed once when `self._task`/`self._task_target` are set (`mastermind.py:154`),
using the night at that moment (`Time.now().night_obs(self._observer)` if `self._observer` is
configured — mirrors `FitsHeaderMixin`'s own `night_obs`/`DAY-OBS` computation, `fitsheader.py:181-184`) — so
it stays fixed for the duration of that observation regardless of how long the task runs or whether
it crosses a night boundary mid-run (an observation started right before local midnight keeps the
`OBSNUM` it was assigned at start).

**Per-frame identifier**: `(OBSNUM, FRAMENUM)` — `FRAMENUM` is unchanged, `OBSNUM` is the new piece
tying frames from possibly-multiple cameras back to one observation. `DAY-OBS` is redundant with the
date already embedded in `OBSNUM`, but stays as-is (existing keyword, other things may depend on it).

**Round-trip `obsnum` onto `Observation` itself — not just the FITS header.** A FITS-only `OBSNUM`
would satisfy "identify the observation from a frame" but not the reverse ("find all frames for
observation X without opening files"), which is the issue's stated goal
("*for data lookup*"). Checked `update_observation()` in all four `ObservationArchive`
implementations to see what this costs:

- **memory** (`memory/observationarchive.py:86-96`) replaces the stored `Observation` wholesale —
  a new field on the model round-trips for free.
- **filesystem** (`filesystem/observationarchive.py:188-202`) rewrites the whole YAML-serialized
  `Observation` — same, free.
- **backend** (`backend/observationarchive.py:178-190`) PUTs `observation.model_dump(use_task_id=True)`
  — but this is **not free**, checked against the actual `pyobs-robotic-backend` repo: its Django
  `Observation` model (`pyobs_robotic_backend/api/models.py:71-85`) has no `obsnum` column, and
  `ObservationSerializer` (`api/serializers.py:83-86`) is a `ModelSerializer` with an explicit
  `fields = ["id", "task", "start", "end", "state", "target"]` allowlist — DRF silently drops any
  key in the PUT body that isn't in that list. Sending `obsnum` today would be a silent no-op, not
  an error. Needs a real change server-side: a new `obsnum` column + migration, and adding
  `"obsnum"` to the serializer's `fields` list. See Migration below.
- **lco** (`lco/observationarchive.py:97-108`) is the one exception: it doesn't round-trip arbitrary
  `Observation` fields at all, it only pushes `state` to LCO's portal API via `ConfigStatus`. A new
  `obsnum` field would never reach LCO's side — but neither does any other field already on the
  model (e.g. `priority`), so this isn't a new gap, just an existing one that also applies here.

**Model field is the compound string.** Add `obsnum: str | None = None` to `Observation`
(`observation.py:28-43`), holding `f"{night:%Y%m%d}-{counter:03d}"`. Self-contained: unlike a bare
int, it doesn't depend on whoever's reading the record also having (and correctly deriving, via
`night_obs()`/observer/timezone) the matching night. `Mastermind` sets
`observation.obsnum = self._obsnum` at the same point it computes the counter (`mastermind.py:154`),
so it's included in the `update_observation()` call already made right after (`mastermind.py:166`) —
no new archive method, no new RPC. This *is* the notification to the backend; no separate
"tell the backend about obsnum" step is needed.

**Ordering already guarantees FITS and backend can't disagree.** `update_observation()`
(`mastermind.py:166`) is not wrapped in try/except, and `_run_thread` is registered with
`restart=True` (`add_background_task(self._run_thread, True)`, `mastermind.py:56`) — per
`BackgroundTask`'s contract (`object.py:345-363`), an uncaught exception there kills and restarts the
whole thread. So if the PUT carrying the freshly-assigned `obsnum` fails, execution never reaches
`self._task_runner.run_task()` (`mastermind.py:171`) for that attempt — no exposures happen, no FITS
file is ever written with an `obsnum` the backend doesn't know about. A failed PUT costs a skipped
number (the same class of gap already noted below for a `FAILED` observation), never a mismatch
between what's in a FITS header and what the archive has on record.

## When is `obsnum` assigned: scheduled, or observed?

Not the same question as counter *placement* above — this is about which `Observation`s get a
number at all.

**Assign only when a task actually starts running (`Mastermind`, current design) — not when an
`Observation` is scheduled.** Checked how often scheduled `Observation`s get discarded before ever
running: `Scheduler._schedule_worker()` (`pyobs/modules/robotic/scheduler.py:203-238`) recomputes
the *entire future schedule* on every `_need_update` trigger — `clear_schedule(start)` wipes
everything from `start` onward, then the whole window is rescheduled from scratch
(`scheduler.py:231-238`). This isn't rare; `_need_update` fires on routine events (new task
submitted, periodic reoptimization, weather/constraint changes), so most `Observation` objects a
scheduler ever creates are speculative and get replaced, often more than once, before their start
time arrives.

If `obsnum` were assigned at `add_observations()` time instead, most of the per-night sequence would
be consumed by `Observation`s that were cleared and re-planned and never produced a single frame —
the numbers would inflate quickly and stop corresponding to actual telescope usage, which is exactly
the correspondence the issue is asking for ("*...for data lookup*" — a lookup key for *data*, not for
scheduling-queue churn). Assigning at task-start keeps the sequence dense and meaningful: every
`obsnum` maps to an `Observation` that actually ran (or at worst failed after starting — the same
class of gap `FRAMENUM` already tolerates when a single exposure fails mid-sequence).

## Migration

- No changes to `ObservationArchive`'s abstract interface or method signatures — `obsnum` travels as
  a field on the existing `Observation` model through the existing `update_observation()` call.
- No changes to `Observation.id` — it stays whatever the archive backend uses it for (UUID, unset,
  etc.); `obsnum`/`OBSNUM` is additive, and this proposal doesn't try to unify the two.
- `Observation` (`observation.py:28-43`) gains `obsnum: str | None = None` (compound form).
- **`pyobs-robotic-backend`**: add an `obsnum` column to the `Observation` model
  (`pyobs_robotic_backend/api/models.py:71-85`, e.g. `CharField(max_length=32, null=True,
  blank=True)`) with a migration alongside the existing ones in
  `pyobs_robotic_backend/api/migrations/`, and add `"obsnum"` to `ObservationSerializer.Meta.fields`
  (`api/serializers.py:85-86`). Without both, `BackendObservationArchive.update_observation()` keeps
  silently dropping the field even after the pyobs-core side ships.
- `Mastermind.__init__` (`mastermind.py:66`) gains a `NightlyCounter` (or equivalent) instance,
  cache path `/pyobs/modules/{self.name}/obsnum.yaml`.
- `Mastermind._run_thread` (`mastermind.py:154`) computes `self._obsnum`, sets
  `observation.obsnum = self._obsnum`, right after `self._task = observation.task` and before
  `TaskStartedEvent`/`update_observation()` — so it's available for the entire duration of the task
  (including any headers requested before the first exposure completes) and persisted to the archive
  in the same call that already records `IN_PROGRESS`.
- `Mastermind.get_fits_header_before` (`mastermind.py:216-220`) adds the `OBSNUM` line shown above.
- If the shared-helper extraction is taken, `FitsHeaderMixin._fitsheadermixin_add_framenum` is
  rewritten to call it instead of inlining the cache read/write — behavior-preserving refactor, no
  header format change for `FRAMENUM`.

## Still open (not resolved by this doc)

- `FitsHeaderMixin`'s current cache logic increments `self._fitsheadermixin_frame_number` in memory
  *before* checking the cache, then overwrites from `cache["framenum"] + 1` if the cache load
  succeeds and the night matches (`fitsheader.py:206-217`) — i.e. the in-memory bump only matters as
  a fallback when the cache read fails. Worth a second look independent of this issue: is that
  fallback intentional (keep incrementing locally if the VFS is briefly unreachable) or incidental?
  Left alone here since #738 doesn't require touching `FRAMENUM` behavior, only reusing its shape.
- What happens if two `Mastermind` instances point at the same night's cache path concurrently (HA
  setup, or a manual restart racing the old process)? `FRAMENUM` has the same latent race today and
  it hasn't been an issue in practice, so not treating this as a blocker — noting it rather than
  designing around it.
- LCO-backed archives never receive `obsnum` server-side (see above) — `OBSNUM` still appears in the
  FITS header for those facilities (computed locally by `Mastermind` regardless of archive backend),
  it just isn't queryable back through the LCO portal. **Decided: ship as a documented gap, not
  gated.** FITS headers are correct everywhere regardless of archive backend; only LCO-backed
  Observation-to-obsnum reverse lookup via the portal is missing, consistent with LCO already
  dropping other `Observation` fields (e.g. `priority`) today. No known requester for that query;
  revisit if one shows up. Fixing it later means extending LCO's `ConfigStatus` push, a separate,
  LCO-specific change.
- A `FAILED` observation (fails immediately after `Mastermind` assigns `obsnum`, before any exposure)
  still burns a number with zero corresponding FITS files. Treated as an acceptable gap, same class
  as a failed exposure leaving a `FRAMENUM` gap — not designing around it here.
