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

### 2. Flaky / slow test sweep

Found one test (`test_filters.py::test_fromlistfilter`) that silently depended on the real
wall-clock date because it patched the wrong `Time.now` -- it only broke when the date rolled
over mid-session. Worth a targeted sweep for the same class of bug: tests using real
`time.sleep`/`asyncio.sleep` instead of a patched one, real network calls, or other
non-deterministic dependencies that could be masking similar issues. Not scoped yet -- would
need its own inventory pass first, same shape as `check_tests.md`/`check_mocks.md`.

### 3. Test coverage gaps

A different question from "are the existing tests good" (which is what the two audits above
covered) -- this would be "which production code paths have no test at all." Not scoped yet.
