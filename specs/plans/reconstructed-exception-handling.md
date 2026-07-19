# Plan: Exception handling across the RPC boundary (reconstructed)

*Reconstructed after the fact from `specs/design/exception_handling.md` (which has its own,
much more detailed "Rollout plan" section — this file is a condensed index into that, not a
replacement for it) and commits `a9deaf29` through `810db63f`. Written after the change landed,
not before it. This was the largest reconstructed change: ~74 files across `pyobs-core` plus
companion fixes in `pyobs-brot`, `pyobs-sbig`, `pyobs-fli`.*

## Goal

Fix three coupled problems in how RPC-boundary exceptions were handled (issue #446): redundant
local logging of an exception the caller already sees; silent type degradation (a non-`PyObsError`
exception collapsing into a generic `RemoteError`, discarding structure); and drift between
documented `Raises:` clauses, the opt-in `@raises(...)` mechanism, and what interfaces actually
raise.

## Architecture

See `specs/design/exception_handling.md` in full — in short: INFO-without-traceback becomes the
default for domain `PyObsError`s raised across the RPC boundary (opt-out via
`_disable_exception_logging` for high-frequency types); reconstructed remote exceptions are
raised as their real registered type instead of wrapped in `InvocationError` (retired
entirely); a `PyobsError` registry replaces `getattr`-based lookup into one hardcoded module,
letting domain exceptions live anywhere; the two catch/log sites collapse into
`Module.execute()`; a correlation id is added for cross-log debugging; and a full interface
docstring audit brings `Raises:` clauses in line with actual behavior.

## File Map (representative, not exhaustive — see commit diffs for the full ~74-file list)

| File | Change |
|---|---|
| `pyobs/utils/exceptions.py` | Core rework: registry via `__init_subclass__`, standardized constructor contract, `PyObsError` → `PyobsError` rename, `InvocationError`/`SevereError` metaclass substitution retired |
| `pyobs/modules/module.py` | `Module.execute()` becomes the single catch/log/classify chokepoint; `_disable_exception_logging`; `_register_exception` instance method (fixes cross-instance global-state bug) |
| `pyobs/comm/xmpp/rpc.py`, `xmppcomm.py` | Fault (de)serialization consults the registry instead of `getattr` on `pyobs.utils.exceptions`; constructor-contract call sites migrated |
| `pyobs/modules/telescope/basetelescope.py`, `_dummytelescopebase.py` | `ValueError` sites → `MissingObserverError`/`AltitudeLimitError`/`InvalidOrbitalElementsError`/`BodyResolutionError` |
| `pyobs/robotic/scripts/exceptions.py`, `pyobs/robotic/task.py`, `storage/lco/task.py` | `ScriptError`; unwrap call sites widened from `InvocationError` to `PyObsError`/`AbortedError` |
| `pyobs/utils/focusseries/photometry.py`, `projection.py` | `FocusModel` gaps → `WeatherDataError`/`FocusTimeoutError`/`MissingSensorError` |
| `docs/source/*` (interface docstrings) | Full `Raises:` audit across every interface |
| `CHANGELOG.rst` | Entries across the multi-commit rollout |

Companion fixes outside this repo: `pyobs-brot` (roof/dome/telescope `init()`/`park()` now raise
`InitError`/`ParkError` on hardware failure instead of silently returning success),
`pyobs-sbig`/`pyobs-fli` (raise `exc.AbortedError` on abort instead of bare `InterruptedError`),
`pyobs-sbig` again (`InvalidArgumentError` on unknown filter name).

## Tasks

- [x] Write design doc (`specs/design/exception_handling.md`, originally
      `DESIGN_exception_handling.md`) and iterate through several rounds of refinement before
      implementation (`6d4b5c70`, `179d2182`, `04291818`, `4bddc149`)
- [x] Step 1: INFO-without-traceback default logging, `_disable_exception_logging` opt-out
- [x] Step 2: registry-based reconstruction, retire `InvocationError`, standardize constructor
      contract, rename `PyObsError` → `PyobsError`, widen the five now-too-narrow catch sites
- [x] Step 3: collapse catch/log sites into `Module.execute()`, retire `SevereError`
      substitution and the `_Meta` metaclass
- [x] Step 4: add correlation id for cross-log debugging
- [x] Step 5: sweep concrete `ValueError`/`NotImplementedError` gaps into named domain exceptions,
      module by module
- [x] Step 6: document the domain/transport split in the module docstring (fix the dead
      docstring-literal bug so `automodule` actually renders it)
- [x] Step 7: document `AbortedError` contract on abortable hooks + driver-repo companion fixes
- [x] Step 8: full interface docstring audit
- [x] Companion fixes: `pyobs-brot`, `pyobs-sbig` (×2), `pyobs-fli`
- [x] Bug found post-rollout: `original_type` didn't actually survive the wire — fixed
- [x] One known, deliberately unaddressed gap: `pyobs-iagvt`'s stale `InvocationError` import
      (now a hard `ImportError` at module load) — left as-is per explicit decision, not tracked
      further here
