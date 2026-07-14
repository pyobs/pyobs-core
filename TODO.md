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

## Needs a design decision

### 1. `Class.__new__(Class)` null test doubles can't go through the constructor

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

## Possible next audits (not scoped yet)

### 2. Test coverage gaps

A different question from "are the existing tests good" (which is what the two audits above
covered) -- this would be "which production code paths have no test at all." Not scoped yet.
