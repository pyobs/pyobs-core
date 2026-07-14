# Testing hygiene TODOs

Forward-looking items from the `check_tests.md` / `check_mocks.md` audits that need a decision
or a chunk of dedicated work, rather than more review. See those two files for the full audit
history (what was found, what was fixed, what was deliberately left alone and why).

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

## Needs a decision

### `Class.__new__(Class)` null test doubles can't go through the constructor

8 files (`test_mastermind.py`, `test_scheduler_mastermind.py`, `test_transit_mastermind.py`,
`test_backend_archives.py`, `test_yaml_archives.py`, `lco/helpers.py`,
`test_schedulereader.py`, `test_schedulewriter.py`) build minimal test doubles via
`Class.__new__(Class)` + manually setting `_comm`/`_observer`/`_timezone`/`_location` to `None`,
bypassing `__init__` entirely.

This is blocked, not just deferred: `Object.__init__` raises `ValueError` for `timezone=None`
(only accepts a string or a real `tzinfo`), so there's no constructor call that reproduces the
state these tests want. Revisit only if `Object.__init__` ever grows a way to represent "no
timezone configured" without raising -- that's a production-code change, not a test fix, and
not clearly worth making just for this.
