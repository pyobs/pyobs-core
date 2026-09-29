# `BaseVideo`: base-owned capture loop, timestamped frames and a frame buffer

Status: implemented in pyobs-core (branch `feature/basevideo-frame-buffer`, 2026-09-29), not yet
merged; driver migration (pyobs-aravis etc.) still open. Plan:
[`2026-09-29-basevideo-frame-buffer-redesign.md`](../plans/2026-09-29-basevideo-frame-buffer-redesign.md).

Repos: pyobs-core (this doc, `BaseVideo`), driver plugins (pyobs-aravis, pyobs-tis, pyobs-v4l,
and the planned video modules in pyobs-asi and pyobs-qhyccd).

Related: [`basevideo-grab-path.md`](basevideo-grab-path.md) and
[`basevideo-live-view.md`](basevideo-live-view.md) build on the frame buffer defined here;
[`guiding-raw-stream.md`](guiding-raw-stream.md) depends on the timestamps.
[`basevideo-raw-frame-streaming.md`](basevideo-raw-frame-streaming.md) (implemented) defines the
current `/video.raw` endpoint. Issues: pyobs/pyobs-asi#46, pyobs/pyobs-qhyccd#81 (new drivers
should be written against this contract).

## Problem

`BaseVideo` (`pyobs/modules/camera/basevideo.py`) has no model of a frame. Every driver runs its
own capture loop and pushes bare numpy arrays with `await self._set_image(data)`
(`pyobs-aravis/pyobs_aravis/araviscamera.py:191`, `pyobs-v4l/pyobs_v4l/v4lcamera.py:119`).
Consequences:

1. **No exposure timing.** `_set_image()` stamps a frame with the time it *arrived*
   (`date_obs = datetime.now(UTC)`), and `grab_data()` uses the arrival time of the *previous*
   frame as `DATE-OBS`. That equals the exposure start only if the camera does not expose the
   next frame during readout and no frames sit in a driver queue. Neither holds for CMOS
   streams: pyobs-aravis, for example, runs with `buffers=5`.
2. **No frame identity.** Nothing carries a frame counter, the exposure time a frame was taken
   with, or which camera settings were in effect. After `set_exposure_time()`, a consumer cannot
   tell whether the next frame already uses the new value.
3. **Duplicated loops.** Activation, error handling and pacing are re-implemented per driver.
4. **Everything runs inside `_set_image()`.** Stack collection, the `grab_data()` handoff and
   JPEG encoding all hang off the push call. The grab path in particular awaits FITS headers
   and the data pipeline there, stalling the stream (see
   [`basevideo-grab-path.md`](basevideo-grab-path.md)).

## Design

### 1. `Frame`

```python
@dataclass(frozen=True)
class Frame:
    data: NDArray[Any]           # owned by BaseVideo from now on, never mutated by the driver
    start: float | None          # exposure start, UTC unix time; None if the driver can't tell
    exposure_time: float | None  # seconds, as actually applied by the camera
    generation: int              # settings generation in effect when the exposure started
```

`BaseVideo` adds, when it receives the frame:

- `number`: monotonically increasing frame counter (replaces `_frame_num`).
- `arrival`: UTC unix time the frame reached `BaseVideo`.
- `start_source`: `"device"` if the driver supplied `start`, `"estimated"` otherwise, where the
  estimate is `arrival - exposure_time - readout_time` (`readout_time` is a new module option,
  default 0). If `exposure_time` is unknown as well, `start` stays `None`.

Consumers get `(number, arrival, start, start_source, exposure_time, generation, data)`.

### 2. Driver contract: an async frame iterator

Drivers implement one method instead of a capture loop:

```python
async def frames(self) -> AsyncIterator[Frame]:
    """Start acquisition, yield frames until closed, stop acquisition in `finally`."""
```

`BaseVideo` owns the loop:

- On activation it starts iterating `frames()`; on deactivation (inactivity, `sleep_time`) it
  calls `aclose()` on the generator, so the driver's `finally` block stops acquisition. This
  replaces the driver-side `_activate_camera()`/`_deactivate_camera()` overrides.
- Exceptions from the iterator are logged; the loop restarts the iterator with a back-off, so
  a USB hiccup doesn't kill the module.
- Blocking SDK calls stay the driver's job (the existing `_run_blocking` pattern in pyobs-asi
  and pyobs-qhyccd); the iterator itself must not block the event loop.
- Ownership: a yielded `data` array must not be reused or mutated by the driver. Drivers that
  recycle SDK buffers copy before yielding. (To verify per driver: whether pyobs-aravis'
  `_array_from_buffer_address()` already copies before the buffer is pushed back.)

### 3. Settings generation

`BaseVideo` keeps an integer `generation`. Drivers call `self._new_generation()` whenever they
change a setting that affects the image (exposure time, gain, offset, window, binning, bit
depth). The driver stamps each `Frame` with the generation that was in effect when that
frame's exposure started. Only the driver can know this: for cameras that restart acquisition
on a settings change it's simply "frames after the restart"; for cameras that apply settings
on the fly it may need to skip the frames still in the pipeline.

Consumers that need a frame taken with current settings (`grab_data()`, the guider after an
exposure-time change) wait for `frame.generation >= generation_at_request`.

### 4. Frame buffer

A small ring buffer of the last `buffer_frames` frames (new option, default 4), plus an
`asyncio.Condition` notified on every new frame. The frame loop does only this:

1. build the `Frame` record (number, arrival, estimated start),
2. apply `flip` (a numpy view, no copy),
3. append to the buffer, notify.

No FITS building, no header requests, no JPEG, no pipeline. Everything else is a consumer:

- `async def wait_frame(predicate, timeout) -> FrameRecord`: first frame, existing or future,
  that matches `predicate`, e.g. `start >= t0 and generation >= g`.
- `async def iter_frames(after: int) -> AsyncIterator[FrameRecord]`: every frame after frame
  number `after`, in order; raises a "frames dropped" error if the consumer falls further behind
  than the buffer holds (used by `grab_stack()`).
- The latest frame, for MJPEG and `/video.raw` (both latest-wins, as today).

Memory: the buffer holds references to at most `buffer_frames` arrays. For large sensors
(e.g. 60 MPix at 16 bit, ~120 MB per frame) the default of 4 is already significant; the option
exists so it can be lowered.

### 5. Timestamps per driver

What each SDK offers, as far as checked:

| Driver | Per-frame timestamp | Notes |
|---|---|---|
| Aravis | Yes, `ArvBuffer.get_timestamp()` | pyobs-aravis' wrapper already exposes it (`aravis.py`, `try_pop_frame(timestamp=True)`), but `AravisCamera` doesn't use it. **To verify:** it's a device clock value (ns) that needs an offset to map to UTC, and at which point of the exposure the camera latches it is model-dependent. Aravis also has `get_system_timestamp()` (host time); which of the two is usable needs a test on real hardware. |
| ASI (zwoasi) | No | zwoasi only wraps `ASIGetVideoData`, which returns no timestamp. The ASI SDK reportedly has GPS variants for GPS-equipped models; not wrapped by zwoasi and not verified. |
| QHY | No | `GetQHYCCDLiveFrame()` returns only w/h/bpp/channels/data (`qhyccd.h`). GPS timing APIs exist for GPS-equipped models only. |
| tis, v4l | Not checked | V4L2 buffers carry a timestamp (`v4l2_buffer.timestamp`); whether the Python bindings in use expose it is not checked. |

So for ASI/QHY the estimate (`arrival - exposure_time - readout_time`) is the realistic option.
Its error is bounded by queueing in the SDK; consumers that care (grab path, guiding) add a
one-frame safety margin when `start_source == "estimated"`.

### 6. Compatibility shim and migration

`_set_image(data)` stays for now as a shim: it wraps `data` in a `Frame(start=None,
exposure_time=<driver's _exposure_time if present>, generation=<current>)` and feeds it into the
same buffer. It logs a one-time deprecation warning. Drivers using the shim keep their own
capture loop and activation overrides unchanged.

Migration order:
1. `BaseVideo` with frame buffer, `frames()` contract and the shim.
2. pyobs-aravis (the only driver family in production use), including device timestamps.
3. New drivers (pyobs-asi, pyobs-qhyccd) directly on the new contract.
4. pyobs-tis, pyobs-v4l, and downstream subclasses of `AravisCamera` in private repos.
5. Remove the shim.

## Considered options

- **Keep push-style `_set_image()`, add optional timestamp arguments.** Smallest change, but
  keeps duplicated loops and still runs consumers inside the push call. Rejected.
- **Unbounded per-consumer queues.** Every consumer sees every frame, but a slow consumer
  (network client) grows memory without bound. Rejected in favour of one shared ring buffer
  with explicit "dropped" errors, matching the latest-wins behaviour of the existing streams.

## Open questions

- Default `buffer_frames`, and whether it should scale with frame size.
- Aravis timestamp semantics (see table): needs a test on the real cameras before the grab path
  or guiding relies on `start_source == "device"`.

## Implementation notes (2026-09-29)

- Code: `pyobs/modules/camera/videoframes.py` (`Frame`, `FrameRecord`, `StartSource`, `FrameBuffer`),
  `BaseVideo._add_frame()`, `_frame_loop()`, `_new_generation()`, `frames()`.
- `buffer_frames` defaults to 4 (open question decided).
- `FrameBuffer` has `wait_frame(predicate)`, `wait_newer(number)` (latest-wins) and
  `next_after(number)` (consecutive, raises `FramesDroppedError`) instead of an `iter_frames()`
  generator.
- The shim takes `exposure_time` from the driver's `_exposure_time` attribute if present, so shim
  frames get an estimated start instead of none.
- `DummyVideo` is the first driver on the new contract.
