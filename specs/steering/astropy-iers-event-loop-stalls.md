# astropy's IERS auto-download can block the event loop from inside basetelescope.py

Same underlying principle as
[blocking-sdk-calls-must-not-run-on-the-event-loop.md](blocking-sdk-calls-must-not-run-on-the-event-loop.md)
-- a synchronous call doing real network I/O, invoked directly on the event loop -- but the
culprit here is a stdlib-adjacent dependency (astropy) called from pyobs-core's own
`basetelescope.py`, not a vendor SDK in a driver repo. Documented separately because the
diagnosis took several wrong turns before landing on the actual mechanism, and because the fix
(a config flag) is different in shape from `_run_blocking()`.

## Symptom

```
[WARNING] (telescope) module.py:205 Event loop stalled for 7.63s -- some call is blocking it.
[WARNING] (telescope) module.py:207 Event loop recovered after being stalled for 9.64s total.
```

Seen on `BrotAltAzTelescope` (`pyobs-brot`) at SAAO (`monet` host), reliably within the first
~15-40s after a module restart, then intermittently afterward. **Only affects modules that
subclass `BaseTelescope`** -- `BrotRoof` (`BaseRoof`) on the same host, hitting the same MQTT
broker, never showed this, which was the clue that ruled out pybrotlib/MQTT as the cause.

## The mechanism (confirmed via `py-spy dump`, not inferred)

`pyobs/modules/telescope/basetelescope.py`'s `_celestial` background task calls
`_update_celestial_headers()` every 30s (first call ~10s after startup), which calls
`self.observer.altaz(...)` / `moon_altaz()` / `sun_altaz()` -- astroplan/astropy coordinate
transforms that need Earth-orientation data (UT1-UTC, polar motion). None of this is wrapped in
`run_in_executor`; it runs directly on the event loop, same as every other line in that function.

astropy's `IERS_Auto` doesn't just check for stale data once at process start -- its
`_refresh_table_as_needed()` re-validates on **every** `pm_xy()` polar-motion lookup, and if it
decides a refresh is warranted, it does the fetch **synchronously and inline**, on whatever
thread called it:

```
Thread 2665202 (active): "MainThread"
    read (ssl.py:1138)
    recv_into (ssl.py:1304)
    readinto (socket.py:719)
    read (http/client.py:484)
    _download_file_from_source (astropy/utils/data.py:1377)
    download_file (astropy/utils/data.py:1550)
    download_file (astropy/utils/iers/iers.py:151)
    _refresh_table_as_needed (astropy/utils/iers/iers.py:870)   <- the actual blocking call
    _interpolate (astropy/utils/iers/iers.py:448)
    pm_xy (astropy/utils/iers/iers.py:410)
    get_polar_motion (astropy/coordinates/builtin_frames/utils.py:46)
    apco (astropy/coordinates/erfa_astrom.py:67)
    icrs_to_observed (astropy/coordinates/builtin_frames/icrs_observed_transforms.py:35)
    __call__ (astropy/coordinates/transformations/function.py:174)
    __call__ (astropy/coordinates/transformations/composite.py:113)
    transform_to (astropy/coordinates/sky_coordinate.py:551)
    altaz (astroplan/observer.py:609)
    _update_celestial_headers (pyobs/modules/telescope/basetelescope.py:822)
    _celestial (pyobs/modules/telescope/basetelescope.py:802)
```

Because this is a **re-check on every lookup**, not a one-time cost at first load, priming the
cache early at startup (what the first two fix attempts here did -- see git history on
`Application._main`'s `_warm_iers_cache`) does not help: the next `pm_xy()` call can still decide
to re-validate and block again, independent of whatever happened at startup. Two rounds of
"prime it earlier" both shipped, both had zero effect on the actual stall -- this is why the
mechanism needed to be caught live rather than reasoned about from timing correlation alone.

## How this was actually found

Log timing alone was misleading -- the stall always landed ~10-30s after "Started successfully",
which pattern-matched the *wrong* hypothesis (network path to the MQTT broker) for a while, then
a *plausible but still wrong* one (the astropy download failing to cache) for two more fix
attempts. What settled it:

1. `py-spy record --pid <pid> --duration 45` aggregated over a whole window mixes normal
   operation with the stall and is hard to read -- the dominant frames by sample count were
   `_update_task` (the MQTT polling loop, genuinely a large fraction of steady-state CPU, but
   *not* the stall) and misc astropy/erfa computation, not obviously "this one thing is blocking
   for 7 seconds."
2. `py-spy dump --pid <pid>`, **polled once per second through the whole risk window**, caught
   the exact frame above mid-stall. A single instant snapshot during an active block is far more
   legible than an aggregate flamegraph -- the blocked thread shows `(active)` and its full stack
   is the one thing frozen in place.
3. Timing the restart script and the `py-spy` launch in **one remote script** (not sequential
   separate SSH round-trips) mattered -- the stall window is only ~15-40s wide, and two earlier
   attempts missed it entirely because `pyobsd restart` + `sleep` + separately fetching the PID +
   launching `py-spy` in separate tool calls burned enough wall-clock time to land after the
   stall had already passed.

## The fix

`iers_offline` config option (added alongside this doc, `pyobs/application.py` +
`pyobs/cli/pyobs.py`): disables `astropy.utils.iers.conf.auto_download` entirely, falling back
to whatever snapshot is installed via the `astropy-iers-data` package (`pyproject.toml`
dependency of pyobs-core; a standalone PyPI package, not bundled inside `astropy` itself, and not
tied to the installed `astropy` version). Set via `pyobs.yaml`:

```yaml
pyobs:
  iers_offline: true
```

Deliberately **not** an env var alone (`PYOBS_IERS_OFFLINE=1` still works, kept for backward
compat) -- modules on `monet` get spawned two different ways (`pyobsd` directly, and
`pyobs-web-admin`'s `subprocess.run`), both `exec`ing the `pyobs` binary directly with no shell
involved, so neither `.profile` nor `/etc/environment` reaches either path, and an env var set in
one launcher's systemd unit wouldn't cover the other. `pyobs.yaml` is read directly by the
`pyobs` binary itself (`pyobs.cli._cli.CLI._load_config`), independent of how it was spawned.

**Maintenance cost this introduces**: with `iers_offline: true`, Earth-orientation accuracy is
frozen to whatever `astropy-iers-data` version happens to be installed -- it never improves on
its own the way a live download would. That package has its own release cadence (independent of
`astropy`/`pyobs-core` releases; its version string embeds the snapshot date, e.g.
`0.2026.7.6.1.1.20` for the 2026-07-06 snapshot) and needs `pip install --upgrade
astropy-iers-data` periodically on any host running with this flag set -- there is no automatic
refresh path once auto-download is off. `iers_conf.iers_degraded_accuracy = "warn"` (set
alongside `auto_download = False`) means a stale/insufficient snapshot logs a warning rather than
failing outright, so this degrades silently in the logs rather than erroring -- worth an
occasional check rather than assuming it stays fine forever.

**Not yet done, structurally more correct**: wrap `_update_celestial_headers()`'s astropy calls
in `run_in_executor`, the same way `_run_blocking()` protects driver SDK calls in the sibling doc.
That would make the loop immune to this class of bug regardless of what astropy decides
internally, and would let live (non-offline) IERS data keep working instead of freezing to the
bundled snapshot indefinitely. `iers_offline` is the shipped stopgap, not the last word.

**Not yet done, rollout**: only applied to `telescope` (`BrotAltAzTelescope`) on `monet` so far.
Any other `BaseTelescope` subclass anywhere in the fleet -- `roof`/`dome` modules are unaffected
since they don't subclass it, but other telescope modules at other sites do run the same
`_celestial` task and are equally exposed.
