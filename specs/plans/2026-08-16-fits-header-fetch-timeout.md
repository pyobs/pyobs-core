# Plan: Bound the FITS-header fetch so a dead peer can't stall the frame

Status: proposed

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

New constructor kwarg `fits_header_timeout: float = 15.0` on `FitsHeaderMixin` (flows through
`ImageFitsHeaderMixin`/`SpectrumFitsHeaderMixin` via `**kwargs`), stored as
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
