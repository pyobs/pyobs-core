# `BaseVideo`: `grab_data()` / `grab_stack()` on top of the frame buffer

Status: proposed (2026-09-29). Not implemented, no plan yet. Depends on
[`basevideo-frame-source.md`](basevideo-frame-source.md).

Repos: pyobs-core (this doc, `BaseVideo`), driver plugins that override `_create_image()` or
`_finish_image()` (pyobs-aravis, pyobs-tis, downstream subclasses).

Supersedes the fix proposed in pyobs/pyobs-core#925.

## Problem

`grab_data()` (`pyobs/modules/camera/basevideo.py:922`) and `_set_image()` hand off a frame
through shared state (`_image_requests`, `_next_image`):

1. **The stream stalls while a requested image is built.** `_set_image()` awaits
   `_create_image()` inline: FITS headers from peers (up to `fits_header_timeout`, 15 s), the data
   pipeline, FITS serialisation and the `NewImageEvent`. Drivers `await _set_image()` from their
   capture loop, so no frames are consumed meanwhile: the MJPEG and raw streams freeze and the
   driver drops or queues frames, which makes the following frames stale.
2. **"Exposure started after the request" is not guaranteed.** Every request in
   `_image_requests` receives the next finished frame, including requests added after
   `_next_image` was armed (i.e. while that frame was already exposing). On top of that, all
   timing is arrival-based (see [`basevideo-frame-source.md`](basevideo-frame-source.md)).
   For acquisition after a slew this can return a frame that was exposing during the move.
3. **Polling and fixed sleeps.** `grab_data()` polls every 10 ms; `_set_image()` sleeps 20 ms per
   waiting request while holding `_image_request_lock` (pyobs/pyobs-core#925).
4. **FITS headers are requested when the previous frame arrives**, not when `grab_data()` is
   called, so their timing depends on the frame rate.

`grab_stack()` already does better: arming and collection are cheap and stay in the frame
path, and the cube is built in the `grab_stack()` coroutine. But it still hooks into
`_set_image()` via `_handle_stack_frame()`.

## Design

`grab_data()` becomes a self-contained coroutine; nothing about it runs in the frame loop.

```python
async def grab_data(self, broadcast: bool = True, **kwargs: Any) -> str:
    await self.activate_camera()
    t0 = time.time()
    generation = self._generation
    image_type, pipeline = self._image_type, self._data_pipeline
    header_futures = await self.request_fits_headers()          # at request time
    frame = await self._frames.wait_frame(
        lambda f: f.generation >= generation and self._started_after(f, t0),
        timeout=...,
    )
    image = self._image_from_frame(frame, image_type, pipeline)  # DATE-OBS = frame start
    await self.add_requested_fits_headers(image, header_futures)
    await self.add_fits_headers(image)
    image, filename = await self._finish_image(image, broadcast, image_type)
    return filename
```

- `_started_after(f, t0)`: `f.start >= t0` if `start_source == "device"`; with an estimated start,
  additionally require `f.start >= t0 + exposure_time` (one-frame margin) to absorb queueing
  error. Frames with `start is None` fall back to "second frame arriving after `t0`".
- Each call is independent: no shared request list, no `_next_image`, no polling, no sleeps.
  Concurrent callers may resolve to the same frame; each builds its own `Image` (open question
  below).
- `DATE-OBS` is the frame's exposure start, not the arrival time of the previous frame.
  `EXPTIME` comes from `frame.exposure_time`. `FRAMENUM` from `frame.number`.
- Timeout: the existing `calc_expose_timeout` stays.
- Headers from peers are requested when `grab_data()` is called, i.e. before the exposure
  starts, matching `BaseCamera`'s `IFitsHeaderBefore` semantics.

`grab_stack()` becomes a consumer with its own cursor:

- Determine `t0`, `generation`, request headers, then find the first qualifying frame with
  `wait_frame()` as above and continue with `iter_frames(after=first.number - 1)` until `count`
  frames are collected.
- Frames must be consecutive (`number` increments by 1); a gap, or falling behind the frame
  buffer, fails the stack with `GrabImageError("frames dropped")` instead of silently stacking
  non-consecutive frames.
- Shape/dtype checks and the memory cap stay as today. Cube assembly happens in the
  `grab_stack()` coroutine. `_handle_stack_frame()`, `StackRequest.armed` and the hook in the
  frame loop go away.
- `abort()` cancels the running `grab_stack()` task as today.

### Subclass hooks

Removed: `NextImage`, `ImageRequest`, `_next_image`, `_image_requests`.

`_create_image(data, next_image)` is overridden by downstream subclasses today. Replacement:

```python
def _image_from_frame(self, frame: FrameRecord, image_type: ImageType, pipeline: str | None) -> Image
```

plus `_finish_image()` unchanged. Subclasses that override `_create_image()` need porting; the
shim period from the frame-source doc covers them (the old hook keeps being called while a driver
uses `_set_image()`).

## Considered options

- **Futures instead of polling, as in #925.** Removes the poll and the sleeps, but the stream
  still stalls during image building and the timing is still arrival-based. Rejected as the end
  state; could still land first as a stopgap if the redesign is far off.
- **Pause the stream and take a real single exposure** (snap mode) for ASI/QHY. Exact exposure
  and settings, but driver-specific, slow on QHY (mode switch likely needs a re-init) and it
  interrupts the live view. Rejected for `BaseVideo`; long single exposures belong to the
  `BaseCamera`-based modules.
- **Build the image in a background task from the frame loop** (keep the loop pushing, move
  `_create_image()` into `asyncio.create_task`). Fixes the stall but keeps the shared-state
  handoff and its bugs. Rejected.

## Open questions

- Concurrent `grab_data()` calls resolving to the same frame: build the image once and share the
  filename (needs matching `broadcast`/`image_type`/`pipeline`), or build per caller? Per caller is
  simpler and the case is rare.
- Whether an estimated start time should be marked in the FITS header, and with which keyword.
