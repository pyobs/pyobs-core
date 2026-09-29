# Plan: `BaseVideo` frame buffer, grab path, live view and stream guiding

Status: in progress. Phases 1, 2, 4, 5 and the server side of 6 implemented on branch
`feature/basevideo-frame-buffer`, merged to `develop` as PR #926 (2026-09-29). Open design questions for those
phases were decided during implementation; see "Implementation notes" in each design doc.

Repos: pyobs-core (phases 1, 2, 4, 5 and server side of 6), pyobs-aravis (phase 3),
pyobs-asi and pyobs-qhyccd (phase 3b, issues pyobs/pyobs-asi#46, pyobs/pyobs-qhyccd#81),
pyobs-tis and pyobs-v4l (phase 7), pyobs-gui and pyobs-web-client (phase 6).

Design docs (source of truth for behaviour, read before starting a phase):
- [`specs/design/basevideo-frame-source.md`](../design/basevideo-frame-source.md)
- [`specs/design/basevideo-grab-path.md`](../design/basevideo-grab-path.md)
- [`specs/design/basevideo-live-view.md`](../design/basevideo-live-view.md)
- [`specs/design/guiding-raw-stream.md`](../design/guiding-raw-stream.md)

Issues: pyobs/pyobs-core#924 (stretch, phase 6), pyobs/pyobs-core#925 (grab handoff, phase 2).

## Ground rules

- Phases 1 and 2 are the core; everything else builds on them. Phases 4 to 6 are independent of
  each other once 1 to 3 are done.
- Checks after every phase: `ruff check pyobs tests`, `black --check pyobs tests`,
  `pyrefly check`, `pytest tests -m "not integration and not xmpp"` (in each touched repo, with
  that repo's equivalents). **Type checker is pyrefly, never mypy.**
- The `_set_image()` shim must keep every unported driver working until phase 8. Test it
  explicitly.
- Downstream `AravisCamera` subclasses in private repos override `_create_image()` and push frames
  themselves; phases 1 to 3 must not break them. Check them before phase 8.
- Do not commit or push. Stop and report if a design doc turns out to be wrong against the code.

## Phase 1: frame record, frame buffer, driver contract (pyobs-core)

Decide first: default `buffer_frames`.

- [x] New `pyobs/modules/camera/videoframes.py`: `Frame`, `FrameRecord` (adds `number`, `arrival`,
      `start_source`), `FrameBuffer` (ring buffer + `asyncio.Condition`, `latest()`,
      `wait_frame(predicate, timeout)`, `iter_frames(after)` raising on overrun).
- [x] `BaseVideo`: `generation` counter and `_new_generation()`; `readout_time` and
      `buffer_frames` options.
- [x] `BaseVideo`: optional `frames()` async iterator; base-owned loop started on activation,
      `aclose()` on deactivation, restart with back-off on errors.
- [x] `_set_image()` becomes the shim: wraps data in a `Frame`, feeds the buffer, one-time
      deprecation warning. Existing `_set_image()` behaviour (grab handoff, stack hook, JPEG)
      stays in place until phase 2/6 replace it.
- [x] MJPEG and `/video.raw` read from `FrameBuffer.latest()` instead of `_last_image`.
- [x] Tests: buffer ordering, overrun error, `wait_frame()` on existing and future frames,
      generation filtering, iterator restart, shim path with a fake push-style driver.

## Phase 2: grab path (pyobs-core)

Decide first: shared vs per-caller image build for concurrent `grab_data()`; header marker for
estimated start times.

- [x] `grab_data()` as a standalone coroutine per [`basevideo-grab-path.md`](../design/basevideo-grab-path.md):
      headers at request time, `wait_frame()` with start-time and generation predicate, image built
      in the caller.
- [x] `DATE-OBS`, `EXPTIME`, `DATE-SRC`, `VIDFRAME` from the frame record, via extra `NextImage`
      fields (no new hook, see grab-path implementation notes).
- [x] `grab_stack()` via `FrameBuffer.next_after()`, consecutive-frame check, overrun error.
- [x] Remove `ImageRequest`, `_next_image`, `_image_requests`, `_handle_stack_frame()`,
      `StackRequest`, `LastImage`, the poll loop and the `asyncio.sleep(0.02)` calls. `NextImage` and
      `_create_image()` stay as the hook for all drivers (see grab-path implementation notes).
- [x] Tests: a request arriving mid-exposure never gets that frame (regression for the late-joiner
      bug), the stream keeps flowing while a slow header peer blocks `grab_data()`, concurrent
      calls, stack gap detection.
- [ ] Close #925 when landed on `develop`.

## Phase 3: pyobs-aravis on the new contract

Issue: pyobs/pyobs-aravis#57.

- [ ] Test on real hardware what `ArvBuffer.get_timestamp()` and `get_system_timestamp()` return
      and when they are latched; decide which to use and how to map to UTC. Record the result in
      the frame-source design doc.
- [ ] Replace `_capture()` / `_activate_camera()` / `_deactivate_camera()` with `frames()`.
- [ ] Copy buffers before yielding if `_array_from_buffer_address()` doesn't already.
- [ ] `set_exposure_time()` and other setters call `_new_generation()`; stamp frames accordingly.
- [ ] Pin the `pyobs-core` floor to the release containing phases 1 and 2.

## Phase 3b: new drivers (pyobs-asi, pyobs-qhyccd)

- [ ] `AsiVideo` per pyobs/pyobs-asi#46, directly on `frames()`; estimated start times.
- [ ] QHY live-mode bindings, verify whether `SetQHYCCDStreamMode()` must precede `InitQHYCCD`,
      then `QHYCCDVideo` per pyobs/pyobs-qhyccd#81.

## Phase 4: raw-stream extensions (pyobs-core)

- [x] `/video.raw` query parameters `x`, `y`, `w`, `h`, `bin`, `max_rate`.
- [x] New meta fields `VIDFRAME`, `DATE-OBS` (start), `DATE-SRC`, `DATE-ARR`, `EXPTIME`,
      `SETGEN`, `CROP-X`, `CROP-Y`, `SWBIN`.
- [x] Per (frame, crop, bin) byte cache.
- [x] Update [`basevideo-raw-frame-streaming.md`](../design/basevideo-raw-frame-streaming.md) wire
      format section.

## Phase 5: stream guiding (pyobs-core)

Decide first: how the guider learns the camera's settings generation; `settle_time` source.

- [x] `GuidingFrameSource` protocol, `GrabDataSource` (current behaviour, moved out of
      `AutoGuiding._auto_guiding()`), `RawStreamSource`.
- [x] `t_settled` tracking after offsets; `not_before` filtering with the estimated-start margin.
- [x] Guider-side header requests (telescope, filter, focus) merged into decoded frames.
- [x] Crop around the guide star, fallback to full frame without a star.
- [ ] Re-centre the crop when the star drifts towards the edge (currently only on reference reset),
      pyobs/pyobs-core#927.
- [x] Tests with a fake raw stream: frames before `t_settled` are skipped, `EXPTIME` filtering,
      missing peer headers skip only their checks.
- [ ] Try on an Aravis-based camera once phase 3 is deployed.

## Phase 6: live view (pyobs-core, pyobs-gui, pyobs-web-client)

Issues: pyobs/pyobs-gui#182, pyobs/pyobs-web-client#58.

Decide first: default mode per client; colour handling.

- [x] pyobs-core: MJPEG query parameters (`stretch`, `cuts`, `lo`, `hi`, `scale`, `quality`),
      module defaults (`linear` + `minmax` replacing `/256`), one encoding per distinct parameter
      set and frame.
- [ ] Close #924 when landed on `develop`.
- [ ] pyobs-gui `videowidget.py`: mode switch (MJPEG / raw), raw decoding in a worker thread,
      live stretch/cut controls, crop on zoom.
- [ ] pyobs-web-client `src/views/VideoView.vue`: same mode switch; raw via streamed `fetch()`,
      canvas rendering; check auth/CORS for `fetch()` against the HTTP-auth design.
- [ ] Check browser connection limits with several cameras on one page.

## Phase 7: remaining drivers

Issues: pyobs/pyobs-tis#23, pyobs/pyobs-v4l#27.

- [ ] pyobs-tis and pyobs-v4l on `frames()`; check whether their bindings expose buffer
      timestamps.
- [ ] Downstream `AravisCamera` subclasses in private repos: port push loops to `frames()`
      (`_create_image()` overrides keep working).

## Phase 8: remove the shim (pyobs-core)

- [ ] Confirm no remaining `_set_image()` callers across the fleet.
- [ ] Remove `_set_image()` and driver-side activation hooks.
- [ ] Release note: breaking change for out-of-tree `BaseVideo` drivers.
