# Plan: Bound the FITS-header fetch so a dead peer can't stall the frame

Status: implemented, closed (merged 2026-08-16, PR #765)
Issue: pyobs-core#764

## Problem

`FitsHeaderMixin.add_requested_fits_headers()` (`pyobs/mixins/fitsheader.py`) awaits every
requested header future in a plain `for` loop with no timeout. The futures are created before the
exposure (`request_fits_headers()`, called from `BaseCamera.grab_data()`) and awaited after readout,
so a peer that never answers its IQ stalls frame finalization for the full XMPP IQ timeout.

That timeout is ~120s (slixmpp's `Iq.send(timeout=None)` default), because `get_fits_header_before`/
`get_fits_header_after` carry no `@timeout` decorator. A `@timeout` decorator would not fix it
anyway: it works by having the *server* reply with a `method_timeout` IQ before running, and a dead
peer never replies at all.

The trigger that surfaced this (issue #764): `admin` was a pyobs-gui on a laptop sent to sleep
without closing the client. Its XMPP session lingered on ejabberd, and `fli230` spent ~120s per
exposure trying to fetch headers from it before giving up and writing the frame without them.

## Design

Bound the whole collection to a single deadline in `add_requested_fits_headers()`, replacing the
sequential `await future` with `asyncio.wait(..., timeout=...)`:

- `asyncio.wait` returns `(done, pending)`. Cancel anything still pending and
  `await asyncio.gather(*pending, return_exceptions=True)` so no lingering task raises an
  unretrieved exception later.
- Skip pending clients with a `timed out` warning, mirroring the existing `RemoteError` path.
- `future.result()` on done tasks; `RemoteError` handling unchanged.

New constructor kwarg `fits_header_timeout: float = 15.0` on `FitsHeaderMixin`, stored as
`_fitsheadermixin_header_timeout`. 15s is generous for live peers (they answer in ms) while keeping
a dead peer from stalling the pipeline for ~120s.

## Testing

`tests/mixins/test_fitsheader.py`:

- a never-resolving peer times out (bounded, task cancelled) and the image is written without its
  headers
- a mix of live + dead peers: live headers added, dead skipped

## Rollout

No server or sibling-repo changes. Configs that don't set `fits_header_timeout` keep the default.
Rollback is removing the kwarg and reverting `add_requested_fits_headers()`.

## Post-merge fixes (review, 2026-08-16)

Two bugs found and fixed on top of the original PR before merge:

- **Empty `futures` crash.** `asyncio.wait()` raises `ValueError` on an empty iterable.
  `request_fits_headers()` returns `{}` for any module with no comm, or no peer implementing
  `IFitsHeaderBefore`/`IFitsHeaderAfter` — a case none of the original tests covered. Fixed by
  skipping the `asyncio.wait` call when `futures` is empty.
- **`fits_header_timeout` didn't reach `BaseCamera`/`BaseVideo`.** Contrary to this doc's original
  claim, `ImageFitsHeaderMixin.__init__` does *not* get `**kwargs` from `BaseCamera`/`BaseVideo` —
  both pass an explicit keyword list (unlike `basespectrograph.py`, which does forward `**kwargs`).
  So a configured `fits_header_timeout` was silently dropped for exactly the module (`fli230`, a
  `BaseCamera`) that motivated this plan. Fixed by adding an explicit `fits_header_timeout` param to
  both and threading it through.

Regression tests added for both, plus a `fits_header_timeout`-reaches-mixin guard for
`BaseSpectrograph` (already correct, previously untested).

Follow-up filed as pyobs-core#767: `add_requested_fits_headers()` only catches `exc.RemoteError`
around each future's result; a peer whose response fails to deserialize for another reason still
crashes the whole exposure rather than just being skipped. Pre-existing behavior, not a regression
from this plan — out of scope here.
