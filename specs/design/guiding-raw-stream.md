# Guiding from the `BaseVideo` raw stream

Status: implemented in pyobs-core (branch `feature/basevideo-frame-buffer`, 2026-09-29), not yet
merged, not yet tried on a real camera. Depends on
[`basevideo-frame-source.md`](basevideo-frame-source.md) (exposure start times, settings
generation) and the raw-stream extensions in [`basevideo-live-view.md`](basevideo-live-view.md) §3
(crop, `FRAMENUM`, `DATE-OBS`, `EXPTIME`, `GENERATION`).

Repos: pyobs-core.

## Problem

[`basevideo-raw-frame-streaming.md`](basevideo-raw-frame-streaming.md) added `/video.raw` so
that guiding could consume frames without the XMPP + VFS round trip, but no guiding module uses
it. `AutoGuiding._auto_guiding()` (`pyobs/modules/pointing/autoguiding.py:79`) still, for every
frame:

1. sets exposure time and image type on the camera via RPC,
2. calls `grab_data()` via RPC (with the problems described in
   [`basevideo-grab-path.md`](basevideo-grab-path.md)),
3. downloads the FITS file through the VFS,
4. processes it (`BaseGuiding._process_image()`, `pyobs/modules/pointing/_baseguiding.py:193`).

For a video camera that already produces frames continuously this adds latency and load per
frame, and the timing information the guider gets is arrival-based.

So far only Aravis-based cameras are candidates for stream guiding. Frame rates and whether
the guider runs on the same host as the camera module are not decided; the design must work in
both cases.

## Design

### 1. Frame source abstraction in `BaseGuiding`

```python
class GuidingFrameSource(Protocol):
    async def next_image(self, not_before: float, generation: int | None) -> Image: ...
```

- `GrabDataSource`: today's behaviour (set exposure/image type, `grab_data()`, VFS read). Default,
  and still used for `BaseCamera`-based guide cameras.
- `RawStreamSource`: keeps one `/video.raw` connection open (VFS path or URL from a new option
  `stream`, same auth as other `HttpFile` access), decodes frames into `Image`s, and returns the
  newest frame matching `not_before`/`generation`. Latest-wins: stale frames are dropped, not
  queued.

`AutoGuiding` picks the source from config (`stream` set or not). `Acquisition` stays on
`grab_data()`; single frames are fine there once the grab path is fixed.

### 2. Discarding frames taken during a correction

After applying an offset, the guider records `t_settled` (when the telescope's offset call
returned, plus an optional `settle_time` option). The next image must satisfy
`DATE-OBS >= t_settled`, with `DATE-OBS` being the exposure start. With
`DATE-SRC == "estimated"`, add a one-frame margin. Without this, a frame exposed during the move
is measured, the same error is corrected twice and the loop oscillates.

This is the main reason the timestamps in [`basevideo-frame-source.md`](basevideo-frame-source.md)
are a prerequisite rather than a nice-to-have.

### 3. Headers the stream doesn't carry

`_process_image()` needs `TEL-RA`, `TEL-DEC` (reset on large separation), `FILTER` (reset on
filter change), `TEL-FOCU` (reset on focus change), `IMAGETYP` and `DATE-OBS`. The raw stream
only carries the camera's local headers, not headers from peers.

The guider fetches those itself: request FITS headers from the telescope/filter/focus modules
concurrently with waiting for the next frame (the same `request_fits_headers()` mechanism the
camera uses), and merge them into the decoded `Image`. Requests happen after `t_settled`, so the
header snapshot matches the frame. If a peer times out, the frame is processed without that
header and the corresponding reset check is skipped, logged once.

`IMAGETYP` is set to `guiding` by the source; the guider no longer needs to call
`set_image_type()` on the camera per frame.

### 4. Exposure time and other settings

The guider's automatic exposure adjustment calls `set_exposure_time()` on the camera only when
the value changes, reads the camera's settings generation afterwards (new field in the camera's
`IExposureTime` state, or returned by the call; to decide) and passes it as `generation` to
`next_image()`, so frames with the old exposure are skipped.

### 5. Crop around the guide star

- The first frame after a (re)start is taken full-frame and becomes the reference.
- The source then reconnects with a crop around the guide star (box size a new option,
  e.g. 128 x 128 px), using `CROP-X`/`CROP-Y` from the metadata to map positions back to full-frame
  coordinates, so `_process_image()` and the offset maths see full-frame coordinates.
- If the star drifts close to the crop edge, re-centre the crop (reconnect). If it's lost, go back
  to full frame and reset the reference.

The crop keeps bandwidth low regardless of where the guider runs, and makes per-frame processing
cheap.

### 6. Dropped frames

`FRAMENUM` gaps are expected (latest-wins) and only logged at debug level. A frame older than
`max_interval` relative to the last processed one resets the reference, as today.

## Considered options

- **Guiding inside the camera module.** Lowest latency, but folds guiding logic into every camera
  driver; the raw-stream design doc already rejected this. Rejected.
- **Keep `grab_data()`, fix only the grab path.** Correct timing after
  [`basevideo-grab-path.md`](basevideo-grab-path.md), but still one RPC plus a VFS download of the
  full frame per guiding step. Kept as the default source, not as the only one.

## Open questions

- Frame rates and host placement of the guider (unknown); decides the default crop size and
  whether full-frame reference frames need `bin`.
- How the guider learns the camera's settings generation (state field vs. return value).
- Whether `settle_time` should come from the telescope module rather than guider config.

## Implementation notes (2026-09-29)

- Code: `pyobs/modules/pointing/guidingsource.py` (`GuidingFrameSource`, `GrabDataSource`,
  `RawStreamSource`); `AutoGuiding` options `stream` (`True` = ask the camera's `IVideo`
  capabilities for the path, or a VFS path), `crop_size`, `settle_time`.
- Settings generation (§4): the guider doesn't read the camera's generation. It compares the
  frame's `EXPTIME` with the requested exposure time instead (1 % tolerance). That needs no
  interface change and covers the one setting the guider changes.
- Crop (§5): the box is placed around the brightest SEP source in a full frame whenever the guider
  has no reference image. There is no re-centring while guiding yet; a lost star only recovers via
  a reference reset.
- Peer FITS headers are requested via the new module-level `request_fits_headers()` in
  `pyobs/mixins/fitsheader.py`, excluding the guider itself.
- `AutoGuiding.stop()` now uses `safe_proxy` for `IExposure`, since video cameras don't have it.
