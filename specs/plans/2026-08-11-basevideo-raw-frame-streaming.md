# Plan: raw-frame streaming endpoint in `BaseVideo`

Status: implemented, closed (merged 2026-08-16, PR #766)
Design: `specs/design/basevideo-raw-frame-streaming.md`

## Context

Design doc above covers the reasoning. This is `pyobs-core` only — no sibling repo work, no
guiding-side consumer, no concrete streaming-camera module (e.g. a future `pyobs-tis` module built
on `BaseVideo`). Just the producer-side changes to `pyobs/modules/camera/basevideo.py` and
`pyobs/interfaces/IVideo.py`.

## Todo

- [x] Fix the existing `video_handler` latency bug first, independently of the new endpoint:
      hardcoded local `interval = 1.0` (`basevideo.py:226`) ignores `self._interval` — decide
      whether to just use `self._interval` there, or keep MJPEG intentionally throttled separately
      from the new raw stream's rate (see next item).
- [x] Add `self._new_frame: asyncio.Event` (or similar name), set at the end of `_set_image()`
      (`basevideo.py:346-393`) on every call. Confirm this is cheap enough to leave unconditional
      (it should be — setting an `Event` with no waiters is trivial) rather than gating it behind
      whether a raw consumer is connected.
- [x] Rename `VideoCapabilities.video: str` -> `mjpeg: str | None = None` (`IVideo.py:10-11`) and
      add `raw: str | None = None`. Breaking rename, no deprecation shim — fine, project is
      `2.0.0.dev`.
- [x] Collapse `live_view: bool = True` + `video_path: str = "/webcam/video.mjpg"`
      (`basevideo.py:79,86`) into a single `video_path: str | None = "/webcam/video.mjpg"`. Drop
      `live_view` entirely — it had no other use in the file. `_set_image()`'s
      `if self._live_view:` (`basevideo.py:368`) becomes `if self._video_path is not None:`.
      `open()`'s capability publish becomes `mjpeg=self._video_path` (fixes the existing bug: today
      it unconditionally advertises `video` even when `live_view=False` means no frame is ever
      emitted, `basevideo.py:170` vs. `:368-374`).
- [x] Register `/` and `/video.mjpg` only when `self._video_path is not None` (currently
      unconditional in `_app.add_routes(...)`) — matches the gating being added for the raw route
      below; `/ping` and `/{filename}` stay unconditional (unrelated to live view).
- [x] Add `raw_path: str | None = "/webcam/video.raw"` to the constructor (mirroring the collapsed
      `video_path` param above) — a single knob, not a bool-plus-path. `None` disables both route
      registration and capability advertisement; a string enables both and is the value passed to
      `VideoCapabilities(raw=self._raw_path)`.
- [x] Register the new raw route, literal path `/video.raw` (mirrors `/video.mjpg`'s hardcoded
      form), only when `self._raw_path is not None`.
- [x] Split `ImageFitsHeaderMixin.add_fits_headers()` (`fitsheader.py:117-134`): pull out the cheap,
      local sub-step (static `fits_headers` dict + `_fitsheadermixin_add_fits_headers()`'s computed
      fields — MJD-OBS/LST/EQUINOX/DAY-OBS/location, no I/O) so it's callable without also running
      `_fitsheadermixin_add_framenum()` (VFS read+write per call). `grab_data()`'s FITS path keeps
      calling the full thing, unchanged. The new raw-stream handler calls only the split-out cheap
      sub-step — see design doc §3 for why the VFS-backed framenum step can't run per frame at
      video rate, and why the raw stream doesn't need any frame-sequence number at all (dropped
      from the wire format, not replaced with an in-memory counter either).
- [x] Implement the new raw-stream handler:
      - multipart response, same `multipart/x-mixed-replace` mechanism as `video_handler`
      - per-frame: JSON meta header built from the split-out cheap header sub-step above (FITS
        keywords — `NAXIS1`/`NAXIS2`/`BITPIX`/`DATE-OBS`/etc., whatever it produces, plus `DTYPE`
        for unambiguous decoding — no `FRAMENUM`) + raw little-endian bytes, per the framing in the
        design doc
      - wait on `self._new_frame`, clear after each read — coalesces backpressure automatically,
        no explicit frame-drop bookkeeping needed
      - call `activate_camera()` on connect; keep updating `_active_time` for the duration of the
        connection, independent of frame arrival (a bounded `asyncio.wait_for` on `self._new_frame`
        re-touches activity on timeout too, not just on frame arrival — otherwise a connected but
        frame-less raw client, e.g. producer paused, could let the camera sleep out from under it)
      - clean up (deregister, let `_active_time` age out normally) on client disconnect
        (`aiohttp.client_exceptions.ClientConnectionResetError`, matching `video_handler`'s existing
        handling at `basevideo.py:248-251`)
- [x] Byte order: confirm outgoing arrays are serialized little-endian regardless of host order
      (explicit dtype cast, not relying on `ndarray.tobytes()`'s native order).
- [x] Add a reconstruction helper (e.g. `Image` classmethod, name TBD) that builds a
      `pyobs.images.Image` directly from `(ndarray, meta dict)` — decode via
      `numpy.dtype(meta["DTYPE"])`, build the `Header` from the FITS-named keys by direct
      assignment. Deliberately does **not** call `Image.from_bytes()`/go through actual FITS
      bytes, and does **not** touch `ImageFitsHeaderMixin`'s namespace-based cross-module enrichment
      — see design doc §3 for why. This is producer/wire-contract scope (`pyobs-core`), not a
      guiding consumer module.
- [x] Lower `sleep_time`'s default from 600s to **60s** (`basevideo.py`, param TBD exact location) —
      a raw-only consumer session that dies previously left hardware streaming for up to 10 minutes
      with nothing consuming it. 60s is a starting point, not measured — flag in a code comment that
      it trades off against `_activate_camera()`/`_deactivate_camera()` cost (driver-specific,
      mostly unknown today) and risks flapping if that cost is high relative to 60s. Stays a single
      global value, not split per consumer type.

## Testing

- Unit test for the new `VideoCapabilities` field (serialization round-trip, matches existing
  capability tests if any exist for `IVideo`).
- Test that `_set_image()` sets `self._new_frame` and that a handler awaiting it wakes.
- Test the coalescing behavior explicitly: multiple `_set_image()` calls while a simulated slow
  consumer hasn't cleared the event yet should not queue multiple wakes.
- Test that connecting to the raw endpoint alone (no MJPEG, no `grab_data()` calls) keeps
  `_active_time` fresh and prevents `_active_update()` from deactivating the module.
- Round-trip test for the new reconstruction helper: `(ndarray, meta)` -> `Image` -> confirm
  `NAXIS1`/`NAXIS2`/`DATE-OBS`/etc. land correctly in `image.header`, and dtype survives.
- Test that the split-out header sub-step used by the raw path does **not** touch the VFS
  (`module.vfs.read_yaml`/`write_yaml`) — the whole point of splitting it out.
- No real hardware needed for any of the above — this is all `BaseVideo`-level, testable against a
  synthetic `_set_image()` feed the way `tests/modules/camera/test_basevideo.py` already does.

## Explicitly out of scope for this plan

- Adapting `pyobs-tis` or any other repo to actually use this.
- A guiding-side consumer of the raw stream.
- WebSocket alternative (see design doc's "Alternatives considered" — not pursuing unless the
  chosen approach proves insufficient).

## Post-merge fixes (review, 2026-08-16)

Three bugs found and fixed on top of the original PR before merge:

- **`raw_handler` liveness.** `_active_time` was only re-touched on frame arrival, so a
  connected-but-frame-less raw client (producer paused, exposure gap) could let the camera go back
  to sleep out from under it, contradicting §5 of the design doc. Fixed by bounding the wait on
  `self._new_frame` with `asyncio.wait_for(..., timeout=self._sleep_time / 2)` and re-touching
  activity on timeout too, not just on frame arrival.
- **`DATE-OBS` stamped at send time.** `_raw_frame()` computed it itself when the handler happened
  to process the frame, drifting from true acquisition time under coalescing or scheduling delay.
  Fixed by capturing it in `_set_image()` at acquisition time and carrying it through the new
  `LastImage.date_obs` field.
- **Missing trade-off comment on `sleep_time`.** The checklist above required flagging the
  `_activate_camera()`/`_deactivate_camera()` cost trade-off in a code comment; it wasn't there.
  Added next to `self._sleep_time = sleep_time`.

One review finding was retracted after verification: iterating `astropy.io.fits.Header` for
`COMMENT`/`HISTORY` cards yields the key once per card, but `header[key]` returns the same full
`_HeaderCommentaryCards` list each time, so the meta-dict build in `_raw_frame()` doesn't lose data
the way it first appeared to.

Follow-up filed as pyobs-core#769: `_raw_frame()` redoes the per-frame header/JSON/byte-copy work
once per connected raw client instead of once per frame and shared. Deferred — precomputing in
`_set_image()` would cost something even with zero raw clients connected, conflicting with the
design's "costs nothing when no raw client is connected" property (§1); the right fix is a lazy
cache keyed by frame number, worth doing once multiple simultaneous raw consumers are a near-term
reality, not needed for this PR's single-consumer case.
