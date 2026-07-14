# Testing hygiene TODOs

Forward-looking items from the mock-usage and private-attribute-access test audits that needed a
decision or a chunk of dedicated work, rather than more review. Everything here is resolved --
kept as a record of what was found/fixed and, where something was deliberately left alone, why.

## Resolved

### `make_xmpp_comm` fixture no longer retrofits comm onto an already-built module ✅

`tests/integration/conftest.py` now has `make_unopened_comm(user)` (a factory fixture building
an unopened `XmppComm`), and `make_module(interfaces, comm, label=...)` takes that comm and
wires itself to it internally, instead of the old `make_xmpp_comm(user, module=None)` building
comm and then retrofitting `module._comm = comm` onto an already-built module. `make_camera_comm`
now just calls `make_unopened_comm("camera")`.

Only `test_xmpp_presence.py` (8 call sites) and `test_xmpp_state.py` (6 call sites) actually
passed a `module` -- the ~30 other `make_xmpp_comm("observer")` call sites across
`test_xmpp_acl.py`/`test_xmpp_dummy_camera.py`/`test_xmpp_rpc.py` never used the `module`
parameter at all and needed no changes. Call sites went from:
```python
module = make_module([ICooling])
camera_comm = await make_xmpp_comm("camera", module)
```
to:
```python
comm = make_unopened_comm("camera")
make_module([ICooling], comm)
camera_comm = await make_xmpp_comm("camera", comm=comm)
```
Verified against a local ejabberd: `pytest tests/integration -m "integration or xmpp"` (72 passed).

### Flaky / slow test sweep ✅

Swept the whole suite for the same class of bug as `test_filters.py::test_fromlistfilter`
(patching the wrong `Time.now`/`datetime.now` target) and other non-determinism sources.
Came back clean -- no fixes applied:

- **`Time.now`/`datetime.now`/`date.today` patch targets** (26 call sites): all correctly patch
  `pyobs.utils.time.Time.now` or a module's own imported reference to that same class, so the
  `test_filters.py` bug was an isolated case, not a systemic pattern.
- **Real `time.sleep()`** (`test_average.py`, 4 call sites): genuinely can't be mocked without a
  patchable time seam in `RollingTimeAverage` (it calls `datetime.now(UTC)` directly). Sleeps are
  short (0.1-0.15s) with a comfortable safety margin over the intervals being tested -- low risk,
  not worth a production-code change just for this.
- **Unseeded randomness**: none found; the one `np.random` usage (`test_curvefit.py`) is seeded.
- **Order-dependent `glob`/`listdir` results**: one file uses unsorted `glob.glob()`
  (`test_yaml_archives.py`), but every assertion on the result either checks length only or
  filters to a single match first -- no test actually depends on result order.
- **Real network calls outside integration-marked tests**: none found.
- **Long `asyncio.sleep()` calls** (including three `asyncio.sleep(100)` in
  `test_background_task.py`): all are the "sleep until cancelled" pattern for testing
  cancellation, not something the test actually waits out.
- **One theoretical, not fixed**: `test_utils_scripts.py::test_log_expression_with_now` compares
  `datetime.now(UTC).year` computed after the script runs against a year value the script baked
  into a log message a few milliseconds earlier -- both call raw `datetime.now(UTC)`, not the
  patchable `Time.now()`. Could theoretically flake in the exact millisecond window UTC year
  rolls over (roughly once every 4 years). Left as-is: negligible real-world risk, and patching
  `datetime` class references correctly is itself easy to get wrong (see the bug this whole sweep
  was triggered by).
- **Aside, not itself flaky**: `tests/modules/filecache/test_http.py` is a single large
  triple-quoted string -- the whole file is inert, pytest collects zero tests from it. Different
  from the `stellarexptime.py`/`standalone.py` collection-glob bugs (those were real tests just
  misnamed); this one was deliberately commented out and would need actual work to turn into a
  real test, not a rename. Not fixed here since it's out of scope for "flaky," not itself broken.

### Test coverage gaps -- scoped ✅

Measured with `coverage.py` (full suite incl. integration/XMPP against a local ejabberd): 60%
overall, 43 files at 0%. Full breakdown, categorized, in `check_coverage.md`. Most of the 0%
files are GUI widgets, CLI entry points, or external-service integrations (Telegram/Matrix/SMB/
SFTP/InfluxDB) -- same cost/value tradeoff that already put XMPP/LCO behind integration markers,
not worth chasing. See `check_coverage.md`'s "Category E" for the real, actionable gaps.

### Tests written for the `pyobs/modules/flatfield/` subsystem ✅

Flagged in `check_coverage.md`: 199 statements across `flatfield.py`/`scheduler.py`/
`pointing.py`, previously **zero test files**. Added `tests/modules/flatfield/` with
`test_flatfield.py` (20 tests: init/open/close/callback/binning/filters/the `flat_field()` state
machine including the already-running guard, abort-mid-run, and telescope-not-ready branches),
`test_pointing.py` (2 tests), and `test_scheduler.py` (5 tests: the `run()` schedule/execute loop,
already-running guard, and mid-item abort). 27 tests total, all passing (`pytest tests/modules/flatfield/`).

`FlatFieldScheduler._scheduler` is a real `Scheduler` instance always built internally from
`functions`/`priorities` (not constructor-injectable), so isolating `FlatFieldScheduler.run()`'s
own orchestration logic from `Scheduler`'s own scheduling algorithm (already covered by
`tests/utils/skyflats/test_scheduler.py`) needed one new private-attribute poke
(`module._scheduler = AsyncMock(spec=Scheduler)`) -- same "no public/constructor path, needed for
isolation" pattern as everywhere else in `check_tests.md`'s Bucket A.

Verified: `pytest tests/ -m "not integration and not xmpp"` (923 passed, up from 896).

### Tests written for `dummymode.py` and `dummyvideo.py` ✅

The last two `Dummy*` simulator modules without tests (their siblings `DummyRoof`/`DummyCamera`/
`MockWeather` all have them). Added `tests/modules/utils/test_dummymode.py` (7 tests: default
modes, open() publishing capabilities/state, set_mode()'s default-group/explicit-group/invalid-
group/closing-during-move branches) and `tests/modules/camera/test_dummyvideo.py` (7 tests:
init defaults, open() publishing exposure-time state, set_exposure_time() including the
exptime<=0 fallback, and the `_frame_task()` background loop's active/inactive branches).

`DummyMode.set_mode()` waits up to 3s in production (`asyncio.wait_for(..., timeout=3.0)`) to
simulate device movement before applying the change -- patched `asyncio.wait_for` directly
(raising `TimeoutError` for "movement completed normally", returning normally for "module started
closing mid-move") rather than actually waiting or poking the private `_closing` event.
`DummyVideo`'s background frame-generation loop is `while True: ... await asyncio.sleep(...)` --
patched `asyncio.sleep` to raise `CancelledError` after one iteration to test a single frame
without running forever, and mocked `_set_image` (a `BaseVideo` method) to isolate the frame
loop's own logic from image/FITS creation, which is `BaseVideo`'s concern, not `DummyVideo`'s.

`BaseVideo.open()` binds a real HTTP port -- mocked out entirely (`mocker.patch.object(BaseVideo,
"open", ...)`) rather than exercised, same as `Module.open()` is mocked out everywhere else.

Verified: `pytest tests/ -m "not integration and not xmpp"` (937 passed, up from 923).

### Tests written for `pyobs/robotic/utils/skyflats/flatfielder.py` ✅

Previously 21.2% coverage (260 statements) despite being the actual flat-fielding algorithm
behind the `FlatField` module. Added `tests/utils/skyflats/test_flatfielder.py` (57 tests)
covering the state machine (`__call__`'s dispatch, `_init_system`/`_wait`/`_testing`/
`_flat_field`, each state's transition/sleep/finish branches), the pure helper methods
(`_eval_exptime`, `_calc_new_exptime`, `_get_image_median`, `_eval_function`, `_initial_check`),
`reset()`, `has_filters`, `_get_bias`, `_take_image`, `_set_window`, and `_analyse_image`.

Isolated each state-machine step from the ones before/after it by mocking the specific private
methods that do the work of adjacent steps (e.g. `_testing()`'s tests mock `_set_window`/
`_take_image`/`_analyse_image` rather than exercising them for real) -- same reasoning as
`FlatFieldScheduler`'s tests mocking out `Scheduler`. `self._eval` (an `ExpTimeEval`, already
covered by `test_exptimeeval.py`) is driven with simple constant-exposure-time functions
(`"5.0"`) rather than mocked, since it's cheap and keeps the tests reading close to real usage;
`self.observer.sun_altaz` is mocked directly since real astronomical calculations would make
test outcomes depend on wall-clock time.

**Found and fixed a real bug while writing these tests**: `_analyse_image()` compared a
normalized fractional deviation (`frac`, typically 0-1ish) against `self._target_count` (a
count-rate, typically ~30000) -- a condition that could essentially never be true, silently
disabling the "retry if the flat is way off target" check. `self._allowed_offset_frac` -- a
constructor parameter clearly named for exactly this purpose -- was stored but never read
anywhere in the file. Fixed `if frac > self._target_count` to `if frac > self._allowed_offset_frac`.

Verified: `pytest tests/ -m "not integration and not xmpp"` (994 passed, up from 937).

### Tests written for `pyobs/modules/camera/basevideo.py`, plus a logic review ✅

Previously 25.7% coverage (206 statements) -- the base class `DummyVideo`/other camera modules
build on. Added `tests/modules/camera/test_basevideo.py` (32 tests) covering init defaults,
`open()`/`close()` (mocking out the real HTTP server bind), the `web_handler`/`ping_handler`/
`image_handler` routes, `camera_active`/`activate_camera`/`deactivate_camera` and the
`_active_update()` auto-sleep background loop, `image_jpeg()`, `create_jpeg()`, `_set_image()`
(flip, live-view JPEG throttling, consuming/preparing `_next_image`), `_create_image()`,
`_finish_image()` (cache write, broadcast), `grab_data()`, and `set_image_type()`.

**Asked to review the logic for soundness while at it -- found four issues, fixed two:**
- **Fixed**: `grab_data()` removed its request from `self._image_requests` without holding
  `self._image_request_lock`, while `_set_image()` iterates and mutates that same list *under*
  the lock in a loop that itself `await`s per iteration (so it genuinely yields mid-iteration).
  A concurrent unprotected `.remove()` during that window could cause another pending request to
  be skipped on that pass. Now `grab_data()`'s removal is also inside the lock.
- **Fixed**: a dead line, `self._image_request = None` (singular -- a typo of `_image_requests`,
  the actual list) that was never read anywhere.
- **Left as a note, not fixed**: `self._new_image_event` is created, `.set()`, and replaced on
  every frame, but nothing in the codebase ever `.wait()`s on it -- vestigial; the real "new
  image" notification path is the separate `NewImageEvent` comm event sent from `_finish_image`.
- **Left as a note, not fixed**: if `filenames=None` is ever configured (nothing enforces this at
  runtime despite the type hint), `format_filename()` returns `None` before ever setting
  `image.header["FNAME"]`, but `_finish_image`'s fallback (`filename = "image.fits"`) still keys
  the cache write off `image.header["FNAME"]` instead of the computed fallback -- would raise
  `KeyError` instead of degrading gracefully. Narrow, config-dependent edge case.

Verified: `pytest tests/ -m "not integration and not xmpp"` (1026 passed, up from 994) and,
against a local ejabberd, `pytest tests/ -m "integration or xmpp"` (still 72 passed).

### Tests written for the pointing/guiding cluster ✅

`pyobs/modules/pointing/_baseguiding.py` (21.7%, 138 stmts), `acquisition.py` (22.2%, 144 stmts),
and `autoguiding.py` (part of the same 22.2% -- `AutoGuiding` is `BaseGuiding`'s only concrete
subclass). `BaseGuiding` itself can't be instantiated directly (`IAutoGuiding` requires
`set_exposure_time`, which only `AutoGuiding` implements), so `tests/modules/pointing/
test_autoguiding.py` (29 tests) exercises both layers together: open()/start()/stop()/
is_running(), the FITS-header/statistics hooks, `_reset_guiding()`/`_set_loop_state()`, the full
`_process_image()` decision tree (disabled/wrong-image-type/first-reference/separation-reset/
filter-change/time-gap-reset/too-soon-ignore/focus-reset/exptime-too-large/apply-success/
apply-not-applied/apply-ValueError/no-telescope-proxy), and AutoGuiding's own `_auto_guiding()`
background loop and `set_exposure_time()`. `tests/modules/pointing/test_acquisition.py` (21 tests)
covers `open()`, `acquire_target()`'s running-flag bracketing (including on exception), the full
`_acquire()` attempt loop (abort/within-tolerance/offset-too-large/apply-and-continue/oneshot/
exhausted-attempts/no-filename/pipeline-error/no-on-sky-distance/exptime-update-from-meta),
`_get_offsets()`'s RA/Dec-then-Alt/Az-then-neither fallback, `_create_log_and_return()`, and
`abort()`.

Verified: `pytest tests/ -m "not integration and not xmpp"` (1076 passed, up from 1026).

### Tests written for `pyobs/mixins/fitsheader.py`, plus two more real bugs fixed ✅

Previously 27.7% coverage (177 stmts) despite being the FITS-header-building mixin used by every
camera module. Added `tests/mixins/test_fitsheader.py` (41 tests) via a minimal `Module +
ImageFitsHeaderMixin` test-double (`BaseVideo` turned out not to forward `frame_number`/
`night_obs` to the mixin at all, so it couldn't exercise those branches -- see below). Covers
`__init__` defaults, `request_fits_headers()`/`add_requested_fits_headers()` (including the
`RemoteError`-skips-that-client path), `add_fits_headers()`'s top-level orchestration,
`_fitsheadermixin_add_fits_headers()`'s MJD-OBS/EQUINOX/location/LST/DAY-OBS logic (both the
night-obs and calendar-day branches), `_fitsheadermixin_add_framenum()` (increment, cache
hit/reset-on-new-night/corrupt-cache/write-failure), `format_filename()`, and
`ImageFitsHeaderMixin`'s WCS-header calculations (CRVAL/CDELT/focal-reduction/CRPIX/CTYPE/PC
matrix, including all the "missing input -> warn and skip" branches).

**Two more real bugs found and fixed while writing these tests:**
- `_fitsheadermixin_add_framenum()` did `hdr["DAY-OBS"]` unconditionally, but `DAY-OBS` is only
  set by `_fitsheadermixin_add_fits_headers()` when `DATE-OBS` was present in the header -- a
  missing `DATE-OBS` meant a `KeyError` crash here instead of the graceful warn-and-skip the
  calling code's log message ("adding NO further information!") implied. Now guards on
  `"DAY-OBS" not in hdr` and warns instead of crashing.
- `_fitsheadermixin_add_fits_headers()` called `date_obs.night_obs(module._observer)`
  unconditionally whenever `night_obs=True` (the default), even if no observer was configured
  (e.g. no `location` given at all) -- `AttributeError: 'NoneType' object has no attribute
  'sun_set_time'`. Now falls back to the plain calendar day when there's no observer to compute
  the night from, same as the existing `location is None` fallback right above it.

Also noted, not fixed (near-zero behavioral risk): `format_filename()`'s `if filename is None:
return None` is unreachable given the underlying utility function's contract (raises `KeyError`
or returns `str`, never `None`); the `ImageFitsHeaderMixin` WCS-header block's `v()` helper checks
`isinstance(k, list \| tuple)` on the *key* (always a plain string at every call site) instead of
the *value* -- looks like a typo, but since `astropy.io.fits.Header.__getitem__` never returns
`(value, comment)` tuples anyway, both branches of the ternary always evaluate identically. Dead,
not currently harmful.

Verified: `pytest tests/ -m "not integration and not xmpp"` (1117 passed, up from 1076) and,
against a local ejabberd, `pytest tests/ -m "integration or xmpp"`.

### Tests written for `pyobs_archive.py` and `local_archive.py` ✅

`pyobs/robotic/utils/archive/pyobs_archive.py` (21.8%, 133 stmts) and `local_archive.py` (29.2%,
89 stmts) -- the two `Archive` backends. `tests/robotic/utils/archive/test_pyobs_archive.py` (18
tests) mocks `aiohttp.ClientSession.get`/`.post` (same pattern as `test_weather_api.py`) to cover
`list_options()`/`list_frames()` (including pagination and non-200 handling), `_build_query()`,
`download_frames()`/`download_headers()`, and `upload_frames()` (including the
zero-created-with/without-errors branches). `tests/robotic/utils/archive/test_local_archive.py`
(16 tests) writes real minimal FITS files into a `tmp_path` and lets `_update_root()`/
`_filter_data()` run for real -- covers directory scanning (including files with missing
headers), `list_options()`, `list_frames()`'s filter-by-everything (start/end/night/site/
telescope/instrument/binning/image_type/rlevel), and `download_frames()`/`download_headers()`.

Verified: `pytest tests/ -m "not integration and not xmpp"` (1150 passed, up from 1117 -- one
unrelated pre-existing failure in `test_basetelescope.py` deselected, from the user's own
in-progress tracking-mode work, not touched here).

### Tests written for `pyobs/modules/robotic/scheduler.py`, plus a real bug fixed ✅

Previously 23.5% coverage (170 stmts) -- only `_compare_task_lists()` had a test before this.
Extended `tests/modules/robotic/test_scheduler.py` (32 new tests) using `AsyncMock(spec=...)` for
the `TaskArchive`/`ObservationArchive`/`TaskScheduler` child objects (`TaskScheduler.schedule()`
is an async generator, so it's stubbed with a plain async-generator function rather than
`AsyncMock`). Covers `open()`/`start()`/`stop()`/`is_running()`, `_update_schedule()`'s
change-detection branches (no change / added / only-current-removed / removed-but-not-scheduled /
removed-and-scheduled), `_schedule_worker()`'s background loop (skip-when-idle, full
schedule-and-submit run including the two-stage `add_observations()` calls and safety-time
recalculation, using the running observation's end as the effective start time, aborting a
schedule pass early when a new update request lands mid-iteration, and catching/logging both
ordinary exceptions and `CancelledError` from within the scheduling try block), `run()`,
`_on_task_started()`/`_on_task_finished()`/`_on_good_weather()`'s event-type guards and
opt-in re-trigger behavior, and `abort()`.

**Found and fixed a real bug while writing these tests**: `_on_task_finished()` is registered in
`open()` as the handler for *both* `TaskFinishedEvent` and `TaskFailedEvent`, but its own guard
was `isinstance(event, TaskFinishedEvent)` -- and `TaskFailedEvent` is a sibling class, not a
subclass, of `TaskFinishedEvent` (both derive directly from `Event`). A failed task was silently
ignored: `_current_task_id` never got cleared and `trigger_on_task_finished` never fired,
regardless of configuration. Fixed to `isinstance(event, (TaskFinishedEvent, TaskFailedEvent))`,
with a regression test (`test_on_task_finished_handles_task_failed_event`).

Verified: `pytest tests/ -m "not integration and not xmpp"` (1220 passed, up from 1150 --
`test_basetelescope.py`'s unrelated failure still deselected) and, against a local ejabberd,
`pytest tests/ -m "integration or xmpp"`.

### `pyobs/modules/camera/basevideo.py`: the two remaining logic-review issues, fixed ✅

The two issues left unfixed from the earlier conservative-scope logic review:
1. Removed `self._new_image_event` (dead code -- created, `.set()`, replaced every frame, never
   `.wait()`-ed on anywhere; confirmed via repo-wide grep).
2. `_finish_image`'s fallback filename (`"image.fits"`, used when `format_filename()` returns
   `None`) wasn't reaching the cache key -- `image.header["FNAME"]` is what's actually used to key
   `self._cache` (and what `image_handler`'s URL lookup matches against), and it was never set in
   that code path, so it'd raise `KeyError` instead of degrading gracefully. Fixed by setting
   `image.header["FNAME"] = filename` alongside the fallback, so the cache write and the URL-based
   lookup stay consistent. (An initial attempt to just cache under the local `filename` variable
   directly was wrong -- that variable holds the full formatted path in the normal case, e.g.
   `/webcam/test.fits`, while the cache/URL lookup is keyed by the bare basename; caught by
   `test_finish_image_writes_to_cache_and_returns_filename` before landing.)

Verified: `pytest tests/modules/camera/test_basevideo.py tests/modules/camera/test_dummyvideo.py`
(39 passed) and full suite `pytest tests/ -m "not integration and not xmpp"` (1229 passed).

### `Mastermind`/`test_mastermind.py`/`test_scheduler_mastermind.py`: `Class.__new__` bypass wasn't actually needed ✅

The "blocked on `Object.__init__` raising for `timezone=None`" reasoning below turned out to be
wrong for these two files -- `timezone` defaults to `"utc"`, not `None`; nobody needs to pass
`None` explicitly. Actually instantiating `MemoryObservationArchive()`/`Mastermind(schedule=...,
runner=...)` confirmed all defaults fall out harmlessly (`comm` -> real `DummyComm()`, `observer`
-> `None`, `timezone` -> real `UTC` tzinfo, none of which anything under test reads).

The one genuine constructor gap: `Mastermind.__init__` typed `tasks: TaskArchive | dict | None =
None` but `add_child_object(None, TaskArchive)` unconditionally raised `TypeError` -- `get_object`
never special-cased `None` for optional child objects the way `Object.__init__` special-cases
`comm=None`/`vfs=None`. And this wasn't just a test inconvenience: `tasks=None` is a legitimate
production configuration (`ObservationArchive.get_next_observation`'s `task_archive` param is
already `None`-safe -- it just skips re-hydrating the task from a canonical archive, fine for
backends like the in-memory/YAML ones where `Observation`s already carry a complete `Task`).
Fixed in `Mastermind.__init__`: `self.add_child_object(tasks, TaskArchive) if tasks is not None
else None`.

With that fixed, replaced the `__new__` bypasses: `QuickRunner`/`FailingRunner` (in
`test_mastermind.py`) had their own custom `__new__` overrides that turned out to be pure
dead weight -- `TaskRunner.__init__` already accepts `observation_archive=None`/`task_archive=None`
as plain defaults (no `add_child_object` involved for those), so removing the overrides entirely
and just calling `QuickRunner()` works. `make_obs_archive()` (duplicated in both files) is now
just `MemoryObservationArchive()`. `make_mastermind()` now calls the real `Mastermind(schedule=
obs_archive, runner=runner, tasks=task_archive)` constructor, keeping only `mm._running = True`
as a plain post-construction poke (skips `open()`/`start()`, which would also register comm event
handlers -- out of scope for what these tests exercise).

Verified: `pytest tests/integration/test_mastermind.py tests/integration/test_scheduler_mastermind.py`
(13 passed) and full suite `pytest tests/ -m "not integration and not xmpp"` (1229 passed).

### `test_transit_mastermind.py`: `TransitQuickRunner` was dead code, removed ✅

Its constructor was also broken independently of the bypass question: `def __init__(self,
end_time): super().__new__(type(self)); self._comm = None; ...` -- calling `__new__` from inside
`__init__` allocates and discards a *new*, unrelated instance; it does nothing to `self`. Turned
out not to matter either way: repo-wide grep found zero instantiations of `TransitQuickRunner`
anywhere. Deleted the class (and the now-unused `QuickRunner`/`Time` imports) rather than fixing
a bypass nobody uses. `TransitImagingScript` itself was already constructed properly via
`model_validate(..., context={"comm": DummyComm()})` -- no bypass involved there.

Verified: `pytest tests/integration/test_transit_mastermind.py` (6 passed, pre-existing unrelated
pyrefly errors on `asyncio.Future()` vs `pyobs.utils.parallel.Future` confirmed via `git stash`).

### `test_backend_archives.py`: `Class.__new__` bypass wasn't needed ✅

Same shape as `Portal`: `BackendTaskArchive`/`BackendObservationArchive.__init__` set
`_aiohttp_session = None` and only populate it in async `open()`. Confirmed by instantiating both
for real (`BackendTaskArchive(url=..., token=..., auto_update=False)`) -- identical resulting
state to the bypass, including `_on_tasks_changed`/`_last_update`/`_projects`/`_tasks` defaults
(the base `TaskArchive.__init__` already defaults `on_tasks_changed=None`). `auto_update=False`
avoids registering the real `_check_for_changes` background task (harmless either way since it's
never started without `open()`, but matches the bypass's original intent exactly). Now both
factories call the real constructor and only override `_aiohttp_session = MagicMock()` after.

Verified: `pytest tests/robotic/storage/backend/test_backend_archives.py` (22 passed).

### `test_schedulereader.py`/`test_schedulewriter.py`: `Class.__new__` bypass wasn't needed ✅

Both `LcoScheduleReader.__init__` and `LcoScheduleWriter.__init__` just store whatever `portal`/
`configdb` they're given (`self._portal = portal`) -- unlike `LcoTaskArchive`/
`LcoObservationArchive` (see below), they don't build their own internally, so the already-fake
`Portal` from `lco/helpers.py::make_portal()` and the already-fake `MagicMock(spec=ConfigDB)` from
`test_schedulewriter.py::make_configdb()` can be passed straight through the real constructor.
The only wrinkle: `LcoScheduleReader.__init__` creates a real `ResolvableErrorLogger` for
`_update_error_log`; tests want a `MagicMock()` there instead, which is a normal post-construction
override, not a reason to skip `__init__` entirely.

Verified: `pytest tests/robotic/storage/lco/` (56 passed).

### `lco/helpers.py`: bypass confirmed genuinely necessary, left as-is

Unlike the reader/writer above, `LcoTaskArchive.__init__` and `LcoObservationArchive.__init__`
both **build their own internal collaborators** rather than accepting pre-built ones:
- `LcoTaskArchive.__init__` always constructs its own `Portal` via `add_child_object(Portal,
  Portal, url=url, token=token, ...)` -- no parameter to inject a pre-built `Portal` with a mocked
  session, and `Portal._session` is only ever populated by the async `open()` method.
- `LcoObservationArchive.__init__` unconditionally does `self._configdb = ConfigDB(configdb)` --
  and `ConfigDB.__init__` does a **real synchronous `requests.get(...)`** to fetch site config at
  construction time. Confirmed by reading `configdb.py` directly; this is genuine network I/O,
  exactly what test doubles are supposed to avoid.

No changes made here -- this is the one file in the original list of 8 where `Class.__new__` is
the right call, not a limitation to route around.

### `test_yaml_archives.py`: verified fixable, fixed ✅

Checked whether this one actually needed the `Class.__new__` bypass, same way as Mastermind.
It didn't, for two different reasons per class:

- `YamlObservationArchive`: no blocker at all. `FileSystemObservationArchive.__init__` just does
  plain OS-path I/O (`os.path.join`, a real `FileLock`, `open()`/`yaml.safe_dump` in the concrete
  subclass) -- it never touches `self.vfs`. Calling `YamlObservationArchive(path=str(tmp_path),
  mode=mode, observer=SAAO)` for real produces the identical shape the bypass built by hand
  (confirmed by instantiating it directly). Now `make_obs_archive()` is a one-line real
  constructor call.
- `YamlTaskArchive`: the `_vfs` fake is legitimate, but for a different reason than comm/timezone.
  `FileSystemTaskArchive.get_schedulable_tasks()` calls `self.vfs.find(self._path, pattern)`, and
  the *real* `VirtualFileSystem` addresses files via configured `"root/relative"` prefixes (e.g.
  `"pyobs/..."`) -- it can't resolve an arbitrary absolute `tmp_path` without registering a custom
  root keyed to that exact path. The fake `vfs.find`/`vfs.read_yaml` (hitting `tmp_path` directly
  via `glob`/`open()`) sidesteps that addressing scheme, not comm/timezone. But that only requires
  faking `_vfs` specifically -- the constructor itself (`YamlTaskArchive(path=str(tmp_path))`)
  works fine for real, so `make_task_archive()` now calls it for real and only overrides `_vfs`
  afterward (an ordinary post-construction poke, same pattern used everywhere else for
  legitimately-mocked collaborators).

Verified: `pytest tests/robotic/storage/filesystem/test_yaml_archives.py` (22 passed) and full
suite `pytest tests/ -m "not integration and not xmpp"` (1229 passed).

Of the original 8 files with `Class.__new__` bypasses, only `lco/helpers.py` still needs it
(see above) -- the other 7 all went through the real constructor once actually tried.

Final tally, full suite: `pytest tests/ -m "not integration and not xmpp"` (1229 passed, 2
skipped -- unchanged, since these were all refactors with no new tests added).
