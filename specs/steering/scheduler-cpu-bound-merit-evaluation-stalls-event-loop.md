# OnDemandScheduler's `evolve()` re-did an uncached astropy sunset lookup on every scheduled task, blocking the event loop directly

Same underlying principle as
[blocking-sdk-calls-must-not-run-on-the-event-loop.md](blocking-sdk-calls-must-not-run-on-the-event-loop.md)
and [astropy-iers-event-loop-stalls.md](astropy-iers-event-loop-stalls.md) -- something holding
the interpreter for too long starves the event loop. This doc originally guessed at a *subtler*
mechanism (GIL contention inside the scheduler's dedicated worker thread) before catching the
actual stall live with `py-spy` -- the real cause turned out to be much more direct: genuine
synchronous astropy computation running **on the main thread itself**, never offloaded at all.
Kept the original wrong hypothesis below (struck through in spirit, not deleted) since the
reasoning for why `ProcessPoolExecutor` isn't a drop-in swap is still valid background for a
related, separate concern -- just not the mechanism behind *this* incident.

## Symptom

```
2026-08-05 11:11:15 [INFO] (scheduler) scheduler.py:247 Finished calculating next task:
2026-08-05 11:11:15 [INFO] (scheduler) scheduler.py:295   - 11:12:14 to 11:30:24: Integrated Sun ...
2026-08-05 11:11:18 [WARNING] (scheduler) module.py:205 Event loop stalled for 0.61s -- some call is blocking it.
2026-08-05 11:11:19 [WARNING] (scheduler) module.py:207 Event loop recovered after being stalled for 2.61s total.
2026-08-05 11:11:22 [INFO] (scheduler) scheduler.py:261 Finished calculating schedule for 52 block(s):
```

Seen on `OnDemandScheduler` (`iagvt`, `scheduler` module) with `iers_offline: true` already
active (confirmed via the startup log line) -- ruling out the IERS network-download stall
documented in the sibling doc. Magnitude is also different: 0.6-2.6s here, vs. 7-10s for the
IERS case. Multiple stalls typically land in one schedule run, scattered between "Finished
calculating next task" and "Finished calculating schedule for N block(s)".

## The mechanism (confirmed live, 2026-08-05, via `py-spy dump --pid <pid>`)

Triggered a real `schedule()` run on the live `iagvt` scheduler process (`pyobs[3982246]`) by
publishing a `TaskFinishedEvent` to fire `Scheduler._on_task_finished`'s
`_trigger_on_task_finished` path, with a `py-spy` burst-sampler (every 0.3s) armed to fire the
moment "Finished calculating next task" appeared in the log. Caught the stall three times across
one run; every capture showed the same thing:

```
Thread 3982246 (active): "MainThread"
    pnm06a (erfa/core.py:11082)
    get_cip (astropy/coordinates/builtin_frames/utils.py:161)
    apco (astropy/coordinates/erfa_astrom.py:69)
    icrs_to_observed (astropy/coordinates/builtin_frames/icrs_observed_transforms.py:35)
    __call__ (astropy/coordinates/transformations/function.py:174)
    __call__ (astropy/coordinates/transformations/composite.py:113)
    transform_to (astropy/coordinates/sky_coordinate.py:551)
    altaz (astroplan/observer.py:609)
    _calc_riseset (astroplan/observer.py:906)
    event_function (astroplan/observer.py:1010)
    _determine_which_event (astroplan/observer.py:1026)
    target_set_time (astroplan/observer.py:1174)
    wrapper (astropy/units/decorators.py:316)
    sun_set_time (astroplan/observer.py:1401)
```

**`MainThread`**, not the `pyobs-scheduler_0` worker thread -- the earlier GIL-contention
hypothesis (below) was about the wrong thread entirely. Traced back through the call chain:
`Time.night_obs()` (`pyobs/utils/time.py:49-65`) calls `observer.sun_set_time(self,
which="nearest")` directly -- a real, uncached astropy computation -- and is called from
`ObservationArchiveEvolution.evolve()` (`pyobs/robotic/scheduler/observationarchiveevolution.py`):

```python
async def evolve(self, scheduled_task: Observation) -> None:
    ...
    night = Time.now().night_obs(self._observer)   # <-- uncached, synchronous, every call
    await self.observations_for_night(night)
    self._obs_for_night[night].append(obs)
```

`evolve()` is called directly from `OnDemandScheduler.schedule()`'s generator loop
(`await data.archive.evolve(task)`), which runs entirely on the caller's event loop -- **never**
routed through `run_cpu_bound()`. Every task scheduled into a run re-triggers this uncached
`sun_set_time()` call; a 52-block schedule does this dozens of times in a few seconds of
wall-clock time, which is exactly the "multiple stalls per run" pattern in the symptom log.

**Fixed**: memoize the result on `ObservationArchiveEvolution` itself (a new instance is created
per `schedule()` call per its own docstring, and "nearest sunset to now" doesn't change across the
few seconds one run takes) -- compute once on the first `evolve()` call, reuse for the rest of the
run. Deliberately *not* switched to `DataProvider.night()` (which already has an `@cache`d
equivalent) despite the apparent duplication: `DataProvider.night()` uses `last_sunset()`
(`which="previous"`), while `night_obs()` uses `which="nearest"` -- different semantics for a time
before any sunset has happened yet (e.g. daytime), so reusing the existing cache would have
silently changed behavior in that edge case. The memoization keeps `evolve()`'s original
`which="nearest"` semantics exactly, just computed once instead of once-per-task.

## Original hypothesis (read from the code, wrong about *which* thread, kept for context)

`pyobs/robotic/scheduler/ondemandscheduler.py`'s `find_next_best_task` /
`check_for_better_task` / `can_postpone_task` all route the actual constraint/merit computation
through `run_cpu_bound()`:

```python
# pyobs/robotic/scheduler/_executor.py
_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="pyobs-scheduler")

async def run_cpu_bound(coro_fn, *args):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(_executor, lambda: asyncio.run(coro_fn(*args)))
```

The guess was that this thread's CPU-bound work could still starve the main thread of GIL time
even while nominally "off the loop." That's a real phenomenon in general, and the reasoning in
the next section about why `ProcessPoolExecutor` isn't a drop-in fix for *that* class of problem
still stands -- but the live capture shows it isn't what produced *this* incident's stalls. If
GIL contention from that worker thread is a real, separate, smaller contributor once the `evolve()`
fix above ships, it would need its own live confirmation the same way this one got one -- not
re-inferred from log timing alone, which is exactly what led this doc astray the first time.

## Why the obvious fix (swap `ThreadPoolExecutor` for `ProcessPoolExecutor`) isn't a drop-in change

A separate process would give real GIL isolation. But `evaluate_constraints_and_merits` isn't
purely CPU-bound -- it runs against a `DataProvider`
(`pyobs/robotic/scheduler/dataprovider.py`) whose cached methods are a mix of two different
things:

- **Pure astropy/numpy math**, no I/O: `sun()`, `moon()`, `sun_altaz()`, `moon_illumination()`,
  `last_sunset()`/`last_sunrise()`. These would parallelize fine in a separate process.
- **Real async network I/O** via `self.archive` (an `ObservationArchiveEvolution`):
  `observations_for_task()` / `observations_for_night()` call
  `await self._obs_archive.get_observations(...)` against a comm-backed `ObservationArchive` --
  a live proxy to another module in the fleet (XMPP), not local data.

That's exactly why `run_cpu_bound` runs `asyncio.run(coro_fn(*args))` inside the thread rather
than a plain synchronous function -- the constraint/merit evaluation genuinely needs an event
loop of its own to await those archive lookups. A `ProcessPoolExecutor` worker can't just receive
that live connection object (not picklable, not meaningfully transferable across a process
boundary), so it would need to open its *own* comm/XMPP connection to do the same lookups --
a materially different architecture (per-worker connection lifecycle, potential JID collisions,
connection setup cost repeated per schedule run) rather than a one-line executor swap.

## Separate, still-open concern: `DataProvider`/`ObservationArchiveEvolution` isn't process-pool-safe

Independent of this incident's actual cause, the reasoning above (archive I/O mixed into what
`run_cpu_bound` treats as CPU-bound work) is still real and still blocks a future
`ProcessPoolExecutor` swap for `evaluate_constraints_and_merits`. See
`specs/plans/scheduler-archive-prefetch-for-process-isolation.md` for that plan -- it now carries
its own note that the specific incident motivating it turned out to have a different, already-fixed
cause, but the picklability/live-connection problem it addresses is real on its own merits and
worth doing regardless of whether GIL contention in the worker thread ever gets its own confirmed
incident.

## Confirmed

`py-spy dump --pid <pid>`, burst-sampled (every 0.3s) starting the instant "Finished calculating
next task" appeared in the live log, triggered on-demand by publishing a `TaskFinishedEvent` rather
than waiting for an organic trigger. Caught the actual mechanism on the first triggered run -- see
above. Same technique as the IERS doc's, adapted to fire on a log-line trigger instead of polling
blind through an uncertain window, since this scheduler's trigger cadence (task-archive-driven,
not a fixed timer) turned out to be too irregular for blind fixed-length polling windows to
reliably land in.
