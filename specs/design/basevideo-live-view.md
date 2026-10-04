# `BaseVideo`: selectable live view, MJPEG for slow links, raw with client-side stretch for fast

Status: server side implemented in pyobs-core (PR #926, merged to `develop` 2026-09-29, not yet
released); pyobs-gui (#182) and pyobs-web-client (#58) not started. Server side depends on
[`basevideo-frame-source.md`](basevideo-frame-source.md) for frame metadata.

Repos: pyobs-core (this doc, `BaseVideo` endpoints), pyobs-gui (`VideoWidget`),
pyobs-web-client (live view).

Related: pyobs/pyobs-core#924 (configurable stretch for 16-bit JPEGs, absorbed here);
[`basevideo-raw-frame-streaming.md`](basevideo-raw-frame-streaming.md) (current `/video.raw`);
[`basevideo-http-auth.md`](basevideo-http-auth.md) (auth stays as designed there);
[`guiding-raw-stream.md`](guiding-raw-stream.md) (uses the raw-stream extensions in §3).

## Problem

The live view is consumed by pyobs-gui, pyobs-web-client and plain browser tabs (the module's
index page). All of them use `/video.mjpg`:

- `create_jpeg()` converts uint16 to uint8 with `data / 256`. For 12 to 16-bit CMOS data of a
  dark sky that's an almost black image (#924).
- The stretch is decided on the server, once, for every viewer. Viewers can't adjust cuts or
  zoom into the data.
- JPEG is 8-bit and lossy, and MJPEG carries no per-frame metadata (frame number, time,
  exposure).

`/video.raw` already delivers full bit depth with a JSON header per frame, but no client uses it
for display, and it always sends the full frame.

Bandwidth differs a lot between deployments: at least one has a constrained uplink, where raw
16-bit frames are not an option, while on a LAN they are.

## Design

The user picks the mode per camera in the client:

- **MJPEG ("low bandwidth")**: server-rendered JPEGs, with stretch controls applied on the server.
- **Raw ("full quality")**: 16-bit frames, stretch and cuts applied in the client, live.

Plain browser tabs keep the MJPEG index page.

### 1. MJPEG with server-side stretch

`/video.mjpg` accepts query parameters, all optional:

| Parameter | Meaning | Default |
|---|---|---|
| `stretch` | `linear`, `sqrt`, `asinh`, `log` | module option `stretch`, default `linear` |
| `cuts` | `minmax`, `percentile`, `manual` | module option, default `minmax` |
| `lo`, `hi` | percentiles (for `percentile`) or ADU values (for `manual`) | 0.5, 99.5 |
| `scale` | downsample factor (1, 2, 4, ...), block mean | 1 |
| `quality` | JPEG quality | 80 |

- The module options give the default for the index page and for clients that don't send
  parameters. The default `linear` + `minmax` replaces `/256` (a behaviour change, but `/256` is
  wrong for anything that isn't a full-range 16-bit signal).
- Encoding is shared per unique parameter set: one encoder task per distinct set that has
  connected viewers, rate-limited by `interval` as today, fed from the frame buffer's latest
  frame. N viewers with the same settings cost one encode.
- Percentiles are computed on a subsampled array (e.g. every 4th pixel in each axis) to keep
  the encode cheap.
- Changing a setting in the client means reconnecting with new parameters. At the frame rates
  involved (at most ~10 Hz) that's acceptable.

### 2. Raw with client-side stretch

The client reads `/video.raw` (extensions in §3), decodes each frame with `numpy.dtype(meta["DTYPE"])`
(GUI) or a typed array (web client), and applies stretch/cuts locally on every frame. Controls:
stretch function, cut mode, lo/hi (slider, updated live without reconnecting), zoom. Zooming in
far enough switches the server-side crop (§3) to save bandwidth.

- pyobs-gui: Qt, decoding in a worker thread, stretch in numpy.
- pyobs-web-client: `fetch()` with a streamed body, multipart parsing in JS, stretch on a
  canvas (WebGL if CPU is too slow for large frames). Auth: `fetch()` can send the Bearer header
  directly; cross-origin use needs the opt-in `cors_origins` option on the module (issue #942,
  see [`basevideo-http-auth.md`](basevideo-http-auth.md)). The client must use the Bearer
  header, the login cookie is not sent cross-origin.

### 3. Raw-stream extensions

Query parameters on `/video.raw`:

| Parameter | Meaning |
|---|---|
| `x`, `y`, `w`, `h` | crop, in unbinned frame pixels; clipped to the frame |
| `bin` | software binning (block mean), after the crop |
| `max_rate` | max frames per second for this connection; newest frame wins |

New fields in `X-Pyobs-Frame-Meta`:

- `FRAMENUM`: frame number, so clients detect dropped frames.
- `DATE-OBS`: exposure start (from [`basevideo-frame-source.md`](basevideo-frame-source.md)),
  plus `DATE-SRC` (`device`/`estimated`) and `DATE-ARR` (arrival time).
- `EXPTIME`, `GENERATION` (settings generation).
- `CROP-X`, `CROP-Y`, `BIN`: so clients map pixel coordinates back to the full frame.

Frame bytes are cached per (frame number, crop, bin), like the existing per-frame cache (#769).

Rough bandwidth, uint16: 2048 x 2048 = 8 MiB per frame; 512 x 512 = 0.5 MiB; at 5 Hz that's
40 MiB/s versus 2.5 MiB/s. On a constrained link, MJPEG with `scale` is the only realistic mode;
raw is for the LAN or for small crops.

## Considered options

- **Keep MJPEG only, with #924's configurable stretch.** Simplest, but viewers still can't
  adjust cuts on full-depth data. Kept as the "low bandwidth" mode rather than the only mode.
- **WebSocket stream with JSON metadata plus image.** Would allow changing crop/stretch without
  reconnecting. Rejected for now: multipart over HTTP already exists (`/video.raw`), works with the
  existing auth, and reconnecting is cheap at these frame rates. Revisit if reconnect latency
  turns out to be annoying.
- **H.264 / WebRTC / HLS.** Inter-frame compression handles noisy low-light frames badly and
  smears faint stars; frame rates are low; WebRTC adds a lot of complexity. Rejected.
- **Lossless compression (zlib/lz4) of raw frames.** Noisy data probably compresses poorly; not
  measured. Left out; could be an optional `encoding` parameter later.

## Open questions

- Default mode in each client (suggestion: MJPEG, with the client remembering the choice per
  camera).
- Browser connection limits: an MJPEG `<img>` or a streamed `fetch()` each hold an HTTP/1.1
  connection; browsers cap those per host (about 6 in Chrome, to be verified). A dashboard with
  several cameras behind one host could hit this.
- Colour cameras: stretch per channel or on luminance.

## Implementation notes (2026-09-29)

- Stretch code lives in `pyobs/utils/stretch.py` (`StretchParams`, `stretch_to_uint8()`), so
  pyobs-gui can reuse it for client-side stretching.
- Cuts: added a `full` mode (the dtype's range; for uint16 within one grey level of the old
  `/256`). Module default `cuts=None` means `full` for 8-bit data and `minmax` otherwise, so 8-bit
  webcams look unchanged.
- No background encoder tasks: the first connection that needs a frame in a given setting
  encodes it (in an executor), all others with the same setting reuse that result.
- Raw meta keys differ from §3, to stay valid 8-character FITS keywords and not clash with the
  nightly `FRAMENUM`: `VIDFRAME` (frame number), `SETGEN` (settings generation), `SWBIN`
  (software binning), plus `DATE-SRC`, `DATE-ARR`, `EXPTIME`, `CROP-X`, `CROP-Y` as designed. The
  crop origin is also written as `XORGSUBF`/`YORGSUBF` before the local headers are built, so
  `CRPIX1/2` are right for the cropped frame.
- Software binning is a block mean, so binned frames are float32.
