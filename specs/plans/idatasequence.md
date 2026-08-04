# Plan: `IDataSequence` — server-side counted data sequences (reconstructed)

*Reconstructed after the fact from `specs/design/idatasequence.md` and commits `3ea9512c`/
`11a9a735` — written after the change landed, not before it.*

## Goal

Give counted image sequences ("take N images") a server-side concept. Previously
`pyobs-gui`'s `CameraWidget.expose()` drove a client-side loop of `grab_data()` calls, so a
client disconnect mid-sequence just stopped it silently, and "abort sequence" vs. "abort
exposure" was a client-only distinction with no server-side equivalent. Tracks #548.

## Architecture

New `IDataSequence(IAbortable)` interface with `grab_sequence()`/`abort_sequence()` and a
pushed `DataSequenceState`, implemented by `BaseCamera`. `grab_sequence()` returns immediately
rather than blocking for the whole sequence — a blocking call's RPC timeout would need to scale
with count, weakening its value as a stall-detection sanity check — and runs the sequence as a
background task, reusing `grab_data()`'s existing FITS/broadcast/upload logic per image.
`abort_sequence()` lets the current grab finish and stops the rest; `abort()` also clears a
running sequence's count. A follow-up added an optional inter-grab `delay` parameter (cadence
control, distinct from dithering/offsets which stay a pointing-layer concern), with both
`abort_sequence()` and `abort()` cutting a pending delay short.

## File Map

| File | Change |
|---|---|
| `pyobs/interfaces/IDataSequence.py` | New interface: `grab_sequence()`/`abort_sequence()`, `DataSequenceState`; later gains optional `delay` parameter |
| `pyobs/interfaces/__init__.py` | Registers the new interface |
| `pyobs/modules/camera/basecamera.py` | `BaseCamera.grab_sequence`/`abort_sequence`/`_run_sequence` — background task, reuses `grab_data()`'s FITS/broadcast/upload path; later gains delay handling |
| `tests/modules/camera/test_grab_sequence.py` | New tests, extended in the follow-up commit |
| `docs/source/whatsnew-2.0.rst` | Documents the new interface |
| `CHANGELOG.rst` | Entry for both commits |

## Tasks

- [x] Write design doc (`specs/design/idatasequence.md`, originally `DESIGN_IDataSequence.md`)
- [x] Add `IDataSequence(IAbortable)` interface with `grab_sequence()`/`abort_sequence()` and
      `DataSequenceState`
- [x] Implement in `BaseCamera` as a background task reusing `grab_data()`'s FITS/broadcast/
      upload logic
- [x] `abort()` clears a running sequence's count
- [x] Add tests
- [x] Follow-up: add optional `delay` parameter for inter-grab cadence control
- [x] Follow-up: `abort_sequence()`/`abort()` cut a pending delay short
- [x] Confirm `pyobs-gui`'s client-side loop migrated to `grab_sequence()` (shipped
      `pyobs-gui@3b43f7c`)
- [x] Resolve `grab_data()` deprecation question as won't-fix (blocking/synchronous-return
      contract isn't interchangeable with `grab_sequence()`'s fire-and-forget one)
- [x] Delete design doc on landing (now restored to `specs/design/` instead, per the new
      persistent-design-doc convention)
