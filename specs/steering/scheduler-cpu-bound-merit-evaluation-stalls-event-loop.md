# OnDemandScheduler's merit evaluation can still stall the event loop, despite already using a worker thread

Same underlying principle as
[blocking-sdk-calls-must-not-run-on-the-event-loop.md](blocking-sdk-calls-must-not-run-on-the-event-loop.md)
and [astropy-iers-event-loop-stalls.md](astropy-iers-event-loop-stalls.md) -- something holding
the interpreter for too long starves the event loop -- but this one is subtler: the offending work
is *already* dispatched to a dedicated worker thread. A thread doesn't give the isolation a
process would; it still shares the GIL with the event loop's own thread.

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
IERS case. The stall lands between logging the first scheduled task and finishing the full
52-block schedule, i.e. during the bulk of `evaluate_constraints_and_merits` calls.

## The mechanism (read from the code, not yet caught live with py-spy)

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

This already exists specifically to keep `evaluate_constraints_and_merits` off the caller's event
loop -- so the mitigation for "blocking work" is already in place. The problem is *which* kind of
isolation a `ThreadPoolExecutor` actually buys you: it moves the work to a different OS thread,
but that thread still shares the single GIL with the event loop's thread. CPU-bound Python/numpy
work (astropy coordinate transforms, evaluated across every task/project/constraint/merit
combination for a whole schedule) can hold the GIL for stretches long enough that the main
thread -- running the event loop -- gets starved of interpreter time even though it isn't
literally blocked on a syscall. That reads as an "event loop stall" from `module.py`'s watchdog
exactly the same as a genuine blocking call would, just smaller in magnitude because the mitigation
does help some (a plain synchronous call directly on the loop would be worse).

This is inferred from the code and log timing, not yet confirmed with a live `py-spy dump` the way
the IERS case was -- see that doc's "How this was actually found" for why a live capture during
the stall window is the reliable way to confirm a hypothesis like this rather than reasoning from
timing correlation alone. Worth doing the same here before investing in a fix.

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

## Not yet done, structurally more correct

Separate the two concerns in `DataProvider` before touching the executor:

1. Prefetch whatever `observations_for_task`/`observations_for_night` need for the tasks/projects
   in play for a given `schedule()` call, up front, on the current async context (real await,
   real network I/O, no GIL contention concern since nothing CPU-heavy is happening
   concurrently).
2. Hand that already-fetched, plain (picklable) data into the constraint/merit evaluation instead
   of leaving it to reach for `self.archive` lazily mid-computation.
3. Only once evaluation no longer needs a live connection does moving it from
   `ThreadPoolExecutor` to `ProcessPoolExecutor` become a real option worth measuring.

This is a bigger change than the IERS fix (a config flag) -- it reshapes how `DataProvider` gets
its archive data, not just where a function call runs. Not attempted yet; this doc records the
constraint so the next person doesn't re-propose the process-pool swap without first hitting the
same picklability wall.

## Not yet done, confirmation

Catch the actual stall live (`py-spy dump --pid <pid>`, polled through the risk window, same
technique as the IERS doc) to confirm GIL contention in the scheduler worker thread is really the
mechanism, rather than something else coincidentally landing in the same log window.
