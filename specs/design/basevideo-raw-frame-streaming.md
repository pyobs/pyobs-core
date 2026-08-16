# `BaseVideo`: raw-frame streaming endpoint, alongside the existing MJPEG live view

Status: implemented

## Problem

`IVideo`/`BaseVideo` (`pyobs/interfaces/IVideo.py`, `pyobs/modules/camera/basevideo.py`) already
covers cameras that push frames continuously rather than on a triggered exposure — a driver calls
`_set_image()` with each incoming frame, `grab_data()` can still promote any one frame to a FITS
file on demand (queues an `ImageRequest`, waits for the next incoming frame,
`basevideo.py:446-483`), and `video_handler` serves a live MJPEG stream over HTTP for humans
watching a browser (`basevideo.py:209-254`).

This came up while planning a `pyobs-tis` (or similarly-shaped) streaming camera module and asking
what else, beyond FITS extraction, a naturally-streaming camera is good for. The concrete case is
guiding: `BaseGuiding`/`BaseAutoGuiding` (`pyobs/modules/pointing/_baseguiding.py`) currently consume
images from a separate camera module via `NewImageEvent` (XMPP comm) + VFS reference, one full
FITS-write-and-fetch cycle per image. That round trip is fine at the cadence a triggered exposure
naturally imposes (seconds), but wrong for a camera already delivering frames at video rate — if
guiding wants to consume that rate, routing every frame through XMPP comm plus a VFS write/read is
both far too slow and puts sustained high-frequency binary traffic on a channel that's a control
plane, not a bulk-data one (see the XMPP fleet's existing fragility under load: iag50's ~7-peer
capability-timeout cascade, tracked separately, not caused by volume but symptomatic of comm being
sensitive to load in general).

## Constraint: one module, one job

pyobs is built as a set of single-purpose modules talking over comm — a camera module exposes and
delivers images, a guiding module computes and applies offsets, they're separate processes/modules
by design. Whatever solves the video-rate consumption problem has to preserve that: it cannot mean
folding guiding logic into the camera module to dodge the RPC cost. The fix has to be a better
*network* path between two still-separate modules, not less separation.

## Proposed change: a second, raw multipart endpoint next to `/video.mjpg`

Reuse the mechanism that already works for MJPEG — an `aiohttp` multipart HTTP stream, one GET per
consumer, each consumer polling/receiving independently — but add a second route serving raw
frames (full bit depth, no JPEG compression) instead of the existing 8-bit JPEG view. A guiding
module becomes an ordinary HTTP client of that endpoint, same relationship a browser already has to
`/video.mjpg`, fully decoupled: the camera module only ever broadcasts, any number of independent
consumers (guiding, a recorder, a second viewer) subscribe without the camera module knowing they
exist.

### 1. Event-driven frame delivery, not polling

`video_handler`'s loop currently busy-polls via `asyncio.sleep(0.01)` and additionally hardcodes a
local `interval = 1.0`, silently ignoring the configured `self._interval` (`basevideo.py:226`) —
already a latency bug worth fixing regardless of this change, since it caps the *existing* MJPEG
view at 1 fps no matter what `interval` is configured to. The new raw handler must not inherit
this: it needs to wake exactly when a new frame lands, not on a fixed poll cadence, or guiding never
sees anything close to the source frame rate.

Add an `asyncio.Event` (e.g. `self._new_frame`) that `_set_image()` sets on every call
(`basevideo.py:346-393`, after `self._last_image` is updated) and that each raw-stream handler
awaits, clearing it after reading. Since `_set_image()` already runs on every incoming frame
regardless of consumers, this costs nothing when no raw client is connected.

### 2. Backpressure: latest-frame-wins, not a queue

Raw frames are much larger than JPEG (a 2048×2048 uint16 frame is ~8 MB vs. a few KB compressed),
so a slow consumer matters more here. Do not queue frames per connection — each handler always reads
`self._last_image` (or a dedicated raw-frame equivalent) at wake time and writes whatever is current,
skipping anything that arrived while a slow `response.write()` was still in flight. Concretely: reuse
the same `asyncio.Event`/clear-on-read pattern from (1), which already coalesces multiple sets into
one wake — a producer calling `_set_image()` five times while a handler is still writing results in
exactly one more wake, with the latest frame, not five queued writes. No new data structure needed
beyond the event itself.

### 3. Wire format (new — nothing in pyobs streams raw binary today)

Multipart, same `multipart/x-mixed-replace` mechanism as the MJPEG stream
(`basevideo.py:220-221`), new boundary and content type. Per part: a small JSON header line
followed by the raw array bytes — human-debuggable (`curl` + eyeballing the header is enough to
sanity-check a stream), no external dependency, and close enough to the existing MJPEG framing
that maintaining both isn't two unrelated protocols.

Every other pyobs method downstream (astrometry, offsets, guiding statistics — everything in
`pyobs.images.processors.*`) operates on `pyobs.images.Image`, i.e. `data` + a real
`astropy.io.fits.Header`. A raw ndarray with an ad hoc metadata blob isn't directly usable by any
of that; the wire format has to let a consumer cheaply reconstruct an `Image`. Two ways to get
there, and they're not equivalent in cost:

- **Send a real FITS file per frame**, via `Image.to_bytes()`/`Image.from_bytes()`
  (`image.py:364`/`181`). Rejected for this: both go through a full astropy `HDUList.writeto()` /
  `fits.open()` each call — real, unmeasured-but-nonzero overhead per frame, paid twice (write on
  the producer, parse on the consumer), on top of FITS's own record-padding overhead in the byte
  stream. Not the right cost to pay at video rate; that machinery exists for the
  already-infrequent `grab_data()` FITS extraction path and should stay there.
- **Chosen: keep the meta JSON, but key it with real FITS keywords**, so building a `Header` from
  it on receipt is a direct field-for-field mapping, not a translation layer:

```
--framebuffer
Content-Type: application/octet-stream
X-Pyobs-Frame-Meta: {"NAXIS1": 2048, "NAXIS2": 2048, "BITPIX": 16, "DTYPE": "uint16", "DATE-OBS": "2026-08-11T22:04:11.123456"}

<raw bytes, row-major, little-endian>
--framebuffer
...
```

`DTYPE` isn't a FITS keyword (FITS only has `BITPIX`, which is signed/lossy for e.g. `uint16`) —
carried alongside so the consumer decodes the raw bytes with `numpy.dtype(meta["DTYPE"])`
unambiguously, then builds the `Header` from the FITS-named keys via straight assignment
(`header[k] = v`). A small helper (e.g. a `pyobs.images.Image` classmethod, name TBD) doing exactly
that — `Image` from `(ndarray, meta dict)` without going through FITS bytes at all — belongs in
this plan's scope, since the wire contract isn't complete/usable until both ends of it are defined,
even though no actual guiding consumer module is being built here.

Header content isn't a fixed, hardcoded minimal set — reuse the same header-building path
`grab_data()`'s FITS extraction already uses (`ImageFitsHeaderMixin.add_fits_headers()`,
`fitsheader.py:117-134`), so a subclass or config's custom headers apply identically to both a FITS
grab and a raw-stream frame, one mechanism, not two. That method is mostly cheap and local — the
configured static `fits_headers` dict, plus `_fitsheadermixin_add_fits_headers()`'s computed fields
(MJD-OBS, LST, EQUINOX, DAY-OBS, observer location, `fitsheader.py:136-184`), no I/O, safe per
frame — **except** it also unconditionally calls `_fitsheadermixin_add_framenum()`
(`fitsheader.py:186-235`), which does a **VFS read + write of a YAML cache file on every call** to
persist a nightly frame-sequence number. That's real I/O, the same class of per-frame cost already
rejected above for `Image.to_bytes()` — calling it unconditionally at video rate would quietly
reintroduce exactly what this design has been avoiding. It's also arguably the wrong concept here:
that FRAMENUM is a nightly-persisted archive sequence number for saved FITS files, not a live
connection's own frame-drop counter.

So: `add_fits_headers()` needs to stop bundling the frame-number persistence into its always-on
path. Split it — a cheap sub-step (static headers + `_fitsheadermixin_add_fits_headers()`'s computed
fields, no I/O) callable on its own, and the existing `_fitsheadermixin_add_framenum()` VFS step
kept only where it already runs today (`grab_data()`'s FITS path, which needs persistent archive
numbering and only runs at exposure cadence). The raw-stream path calls only the cheap sub-step —
no `FRAMENUM` at all for the raw stream, no substitute counter either: a live video frame doesn't
need a persistent sequence number the way an archived FITS file does, and nothing downstream (§1/§2's
event-driven, latest-frame-wins delivery) depends on one. Dropped from the wire format above.

Still explicitly **not** reused here: `request_fits_headers`/`add_requested_fits_headers`
(`fitsheader.py:60-115`), the namespace-based cross-module header fetch used by `_create_image` for
the FITS-extraction path (`basevideo.py:394-414`) — that one does a comm round-trip to other modules
per image and is sized for the infrequent FITS-grab cadence, not per-frame at video rate. Only the
local/static half of the header pipeline is shared between the two paths, not the networked half.

Byte order: always little-endian on the wire (`.astype(..., copy=False)` / explicit `<u2` etc. as
needed), don't rely on host native order — a consumer on different hardware would silently
misdecode otherwise.

### 4. Capability advertisement: `mjpeg`/`raw`, both `str | None`, on by default

`VideoCapabilities` (`pyobs/interfaces/IVideo.py:10-11`) currently has one field, `video: str` (the
MJPEG path), always populated. Reshaped to:

```python
@dataclass
class VideoCapabilities:
    mjpeg: str | None = None
    raw: str | None = None
```

`video` -> `mjpeg` for clarity now that there are two paths, and not `fits` — the wire format (§3)
is explicitly *not* real FITS bytes (that was the whole point of not using `Image.to_bytes()` per
frame), so naming the field `fits` would tell a consumer they can hand the stream to a generic FITS
reader, which they can't. This is a breaking rename with no deprecation shim — acceptable, project
is `2.0.0.dev`.

Both fields are `str | None` rather than always-populated `str`, for two different, concrete reasons
(not "just in case" on either):

- **`mjpeg`** — fixes an existing bug, independent of the raw-stream work, and once fixed exposes
  the same one-knob-not-two redundancy just resolved for `raw`. `BaseVideo` currently has *two*
  separate constructor params for this: `live_view: bool = True` (`basevideo.py:86`), gating
  whether `_set_image()` computes a JPEG at all (`basevideo.py:368-374`, `live_view`'s only use in
  the file), and `video_path: str = "/webcam/video.mjpg"` (`basevideo.py:79`), the string
  unconditionally advertised as the capability (`basevideo.py:170`, regardless of `live_view` — the
  bug: a module built with `live_view=False` today advertises a working MJPEG endpoint that never
  emits a frame). The two params encode exactly one degree of freedom. Collapse to a single
  `video_path: str | None = "/webcam/video.mjpg"`, drop `live_view`: `None` means don't compute
  JPEG and don't advertise `mjpeg`; a string means both.

  Also fixes an asymmetry the `raw` design otherwise wouldn't share: MJPEG's routes (`/`,
  `/video.mjpg`) are registered unconditionally today — hardcoded in `_app.add_routes(...)`, not
  actually gated by `live_view` or `video_path` at all. Since the constructor signature is already
  changing here, register `/` and `/video.mjpg` only when `self._video_path is not None`, matching
  how `raw`'s route registration is gated on `raw_path is not None`. `/ping` and `/{filename}`
  (`image_handler`, serving cached FITS via `grab_data()`) are unrelated to live view and stay
  unconditional.
- **`raw`** — the raw-stream mechanism itself is generic to every `BaseVideo` subclass (`_set_image()`
  already receives a raw ndarray from every subclass regardless of driver, so there's no subclass
  for which it technically wouldn't work — nothing to gate on that basis) and nothing in pyobs does
  automatic capability-driven attachment of consumers (checked: capabilities feed `pyobs-gui` widget
  selection and presence info, not robotic auto-wiring; guiding modules get their camera reference
  from explicit config, a proxy name, not by scanning capabilities) — so by default this should just
  be on. But an operator at a genuinely bandwidth-constrained site may want to hard-disable it rather
  than rely on nobody connecting: a raw frame is far heavier than JPEG (~8 MB vs. a few KB for a
  2048×2048 uint16 frame), and someone pulling that over a constrained link without realizing the
  cost is a real, if minor, foot-gun.

  Not a separate `raw_stream: bool` flag alongside the path, though — that would be a bool
  duplicating information `raw: str | None` already carries in full. One knob instead, mirroring how
  `video_path: str = "/webcam/video.mjpg"` already works for MJPEG (a path, not a path-plus-bool):
  add `raw_path: str | None = "/webcam/video.raw"` to the constructor. `None` disables route
  registration and capability advertisement together; a string both enables it and *is* the value
  passed straight to `VideoCapabilities(raw=self._raw_path)` — on by default (non-`None`), explicit
  opt-*out* by passing `None`.

  The literal `aiohttp` route registered is `/video.raw`, the same fixed short form `/video.mjpg`
  already uses (`basevideo.py:151`) — mirroring existing precedent, not introducing a new one.
  Note this route string and the `raw_path`/`video_path` *capability* value aren't necessarily the
  same string (existing MJPEG behavior already works this way: the route is hardcoded `/video.mjpg`
  regardless of what `video_path` is configured to); `video_path`/`raw_path` line up with VFS root
  naming on the consuming side per the class docstring, a separate concern from this server's own
  route table. That indirection predates this change and isn't being touched here.

### 5. Activate/deactivate wiring

`BaseVideo` already has an activity-tracking mechanism to avoid streaming 24/7: `activate_camera()`/
`deactivate_camera()`, `_active`/`_active_time`, a background `_active_update()` task that
deactivates after `sleep_time` (default 600s) of no activity, and overridable `_activate_camera()`/
`_deactivate_camera()` hooks for subclasses to actually start/stop hardware
(`basevideo.py:283-314`). Currently only `image_jpeg()` (`basevideo.py:316-323`) and `grab_data()`
(`basevideo.py:461`) touch `_active_time`.

The new raw handler must call `activate_camera()` on connect and keep touching `_active_time` for as
long as it's serving frames (mirroring what `video_handler`'s loop already does via `image_jpeg()`),
or a guiding session that exclusively uses the raw endpoint never registers as activity and the
camera goes back to sleep out from under an active guider once `sleep_time` elapses. `_active`/
`_active_time` stay a single shared flag across all consumers (MJPEG viewer, raw consumer, FITS
grabs) — any one of them keeps the hardware running, which is the correct behavior, no new state
needed there.

`sleep_time`'s default is changing from 600s to **60s**: a raw-only guiding session that dies
(crash, network drop) previously left hardware streaming for up to 10 minutes with nothing
consuming it; that's too long once the raw stream can be the sole thing keeping a module active.
60s is a starting point, not a measured number — it trades off against `_activate_camera()`/
`_deactivate_camera()` cost, which is driver-specific and mostly unknown right now (e.g. TIS's
pipeline start/stop hasn't been exercised against real hardware yet, per the driver/GUI-split plan).
Too short a `sleep_time` relative to that cost risks flapping — rapid activate/deactivate cycling if
a consumer's reconnects are slower than the grace period. Revisit this number once a real driver's
activate/deactivate cost is known; `sleep_time` stays a single global value shared by MJPEG/raw/FITS
activity, not split per consumer type — simpler, and nothing so far justifies the extra state.

## Alternatives considered

- **In-process guiding inside the camera module.** Rejected — contradicts the one-module-one-job
  principle pyobs is built on; was the first thing suggested in discussion and correctly pushed
  back on.
- **Per-frame `NewImageEvent`-style broadcast over XMPP comm.** Rejected — comm is a control-plane
  pub/sub, not sized for continuous high-frequency binary payloads, and the XMPP fleet is already
  sensitive to load (see the iag50 capability-timeout investigation). Keeping bulk frame data on a
  plain HTTP connection, entirely outside the comm/XMPP path, avoids that risk.
- **WebSocket push instead of multipart HTTP.** More natural fit for a "server pushes, client
  reads" backpressure/close model, and `aiohttp` supports it natively (no new dependency). Not
  chosen for now because nothing else in pyobs uses WebSockets, while multipart-over-HTTP is
  already precedented (the MJPEG endpoint) — lower risk to extend an existing pattern than to
  introduce a second one. Worth reconsidering if the coalescing-event backpressure approach above
  turns out to be insufficient in practice.

## Open questions / not yet decided

- No consumer-side (guiding) work is in scope here — this only covers the producer side in
  `pyobs-core`. A guiding-side client for this protocol is a separate, later piece of work.
