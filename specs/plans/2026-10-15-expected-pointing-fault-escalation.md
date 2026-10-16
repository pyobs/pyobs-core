# Expected pointing faults and remote-error escalation

Status: implemented; merged to develop in [PR #1000](https://github.com/pyobs/pyobs-core/pull/1000) on 2026-10-15; not yet released

Repos: pyobs-core

Issue: [pyobs-core#959](https://github.com/pyobs/pyobs-core/issues/959).

## Problem and evidence

`BasePointing` registers `RemoteError` handlers for its camera and telescope;
`FlatField` does the same for camera, telescope and optional filters. All use
three occurrences within 600 seconds and `_default_remote_error_callback()`,
which sets the caller to `ModuleState.ERROR`.

In `pyobs/modules/module.py`, `_store_exception()` adds a synthetic `RemoteError`
bucket for every remotely tagged domain error. `_exception_matches()` likewise
matches every remotely tagged error against `RemoteError`. Consequently
`AltitudeLimitError`, despite inheriting from core `PointingLimitError` rather
than `MotionError`, still counts towards these broad caller-side handlers.
The core class explicitly describes a rejected destination with no attempted
movement and a healthy device; repeated rejection is not evidence of failure.

A local reproduction on 2026-10-15 exercised a real
`DummyRaDecTelescope.move_radec(0, -80)` with observer latitude 52 degrees,
longitude 10 degrees, elevation 100 m and motion status mocked to TRACKING.
A minimal `BasePointing` + `IAbortable` caller reconstructed the resulting fault
with `rpc.reconstruct_fault()` and raised it through `execute("abort")`.
The caller used named camera/telescope dependencies, an empty pipeline,
`ApplyOffsets()` and initial READY state. Attempts one and two produced remote
counts one and two while remaining READY; attempt three reached count three,
ran the real severe-error callback and entered ERROR. The exception remained
`AltitudeLimitError`, never `MotionError`. This used no live XMPP or hardware.

## Design and boundaries

Exclude the `PointingLimitError` family only from the synthetic broad
`RemoteError` severity classification. Apply the same rule to recording and
callback matching: fixing counts alone still allows an expected fault to fire
a handler whose earlier genuine failures already reached the threshold.

Use the existing core ancestor, so both imported driver leaves and RPC fallback
to `PointingLimitError` receive identical treatment. Keep normal inheritance
matching: explicitly registered `PointingLimitError`, leaf-type or `PyobsError`
handlers may still count these faults and run their chosen callbacks. Preserve
exception propagation, remote metadata and ordinary logging.

Make this a narrow shared `Module` policy, which also protects other consumers
of the broad remote handler. A per-registration `exclude` API is unnecessary
for this established expected-condition contract and would require reconciling
different exclusion lists with the current shared per-type counter buckets.
Do not exempt all domain faults, or add speculative exclusions for `AbortedError`,
weather, script or other conditions. Keep genuine `RemoteError` subclasses,
remote `GrabImageError`, `MotionError` and unclassified failures eligible.
No RPC schema, hierarchy, driver, threshold or configuration change is needed.
Legacy faults reconstructed as `UnclassifiedError` remain eligible; do not infer
safety from error text or `original_type` strings.

## Implementation checklist

- [x] In `Module`, centralize eligibility for synthetic `RemoteError` matching
      and reuse it from `_store_exception()` and `_exception_matches()`.
      Preserve actual `isinstance()`/MRO matches and existing local/remote
      storage keys; only suppress the synthetic classification for
      `isinstance(exception, exc.PointingLimitError)`.
- [x] Leave `BasePointing` and `FlatField` registrations at 3/600 seconds.
      Keep their default callback and normal fault propagation unchanged.
- [x] Update `_register_exception()`/matching/storage documentation and
      `docs/source/recipes/exceptions.rst`, whose current claim that broad
      remote handlers count *every* remote error needs the specific exception.
      Clarify the core `PointingLimitError` docstring to cover broad remote
      escalation as well as motion escalation.
- [x] Add focused regressions in `tests/modules/test_exception_logging.py`:
      repeated tagged core and leaf pointing-limit faults never populate the
      `RemoteError` bucket or invoke its callback; explicit domain handlers
      still count and fire, including local handlers for local faults.
- [x] Reconstruct an unknown driver leaf with the core ancestor in `bases`;
      assert ancestor selection, retained `original_type`/`remote_module`,
      excluded broad escalation and functioning explicit ancestor handling.
      Keep existing reconstructed `MotionError` and remote `GrabImageError`
      tests as positive controls.
- [x] Cover a mixed sequence of genuine failures and pointing-limit faults:
      only genuine failures advance the broad counter. After that counter
      reaches its limit, another pointing-limit fault must not schedule its
      callback. Use callback events or awaited task completion, and a patched
      clock for the 600-second boundary rather than long sleeps.
- [x] Verify real transport errors still reach the threshold, old eligible
      events age out, and counters stay scoped to the configured remote name
      and module instance. Preserve handlers without `module=` as local-only.
      Do not refactor unrelated callback behavior as part of this change.
- [x] Add caller-level regressions using the actual constructor registrations
      for both `BasePointing` and `FlatField`. Reuse the existing flat-field
      mock `FlatFielder` fixture pattern and a minimal abortable pointing caller.
      Exercise reconstructed faults through `execute()`, await scheduled
      callbacks and assert three expected rejections leave READY/error string
      unchanged. With fresh callers, three genuine failures must invoke the
      real default callback and enter ERROR. Cover named camera/telescope and
      flat-field filter registrations with appropriate positive failures.
- [x] Retain one offline reproduction with the real dummy telescope altitude
      guard to connect the classification regression to the original trigger;
      freeze time and disable IERS downloads. No live XMPP service is necessary.

## Verification and acceptance

Run in the repository development environment after implementation:

```sh
pytest tests/modules/test_exception_logging.py tests/comm/test_rpc_serialization.py tests/utils/test_exceptions.py tests/modules/pointing tests/modules/flatfield tests/modules/telescope
ruff check pyobs tests
black --check --workers 1 pyobs tests
pyrefly check
pytest tests -m "not integration and not xmpp"
```

- [x] Record actual results and any environment limitations; update this plan
      and its index after implementation.

Acceptance: repeated known pointing-limit rejections neither accumulate in
broad remote-failure counters nor trigger those callbacks, even after genuine
failures have already reached the threshold. Explicit domain handlers remain
available. Genuine motion, acquisition and transport failures retain threshold,
timespan and counter-scoping behavior, and still put the affected caller into
ERROR through its existing callback.

No blocking questions remain for this narrow fix. Additional expected-condition
families or caller-specific exclusion policies need separate evidence and scope.
Implementation is complete in an isolated worktree on
`codex/959-expected-pointing-faults`; verification results are recorded below.


## Implementation verification (2026-10-15)

- Centralized synthetic remote-failure eligibility in `Module` and used it for
  both severity storage and callback matching. Actual inheritance and explicit
  domain handlers retain their existing behavior. Caller registrations remain
  at three faults within 600 seconds.
- Added 20 regression cases across the exception tests and a dedicated caller
  test file, including unknown driver ancestor fallback, mixed sequences after
  threshold, clock-controlled expiry/scoping, actual pointing/flat-field
  constructors, and a real dummy-telescope altitude rejection.
- The focused exception/RPC/pointing/flat-field/telescope suite passed: 240 tests.
  The new core/leaf regressions fail against the original severity methods
  restored in memory, confirming that they detect the reported behavior.
- Ruff, Black (761 files) and Pyrefly pass. Pyrefly uses the existing project
  virtualenv explicitly, since this worktree has no separate environment.
- Full non-integration suite: 2,512 passed, 26 skipped, 102 deselected and one
  expected failure (9 warnings). Use the installed `pytest` launcher: existing
  daemon CLI tests find `pyobs` beside `sys.argv[0]` and fail under `python -m
  pytest`. The final run used the installed launcher and passed without
  application changes for that environment issue.
