# `IDataStack`: grab a stack of consecutive frames into one product

Status: proposed (2026-09-27). Not implemented. Plan:
[`2026-09-27-data-pipeline-stack-reset.md`](../plans/2026-09-27-data-pipeline-stack-reset.md).

Repos: pyobs-core (interface, `Image`, `BaseCamera`, `BaseVideo`), driver plugins (inherit it via
the base classes).

Related: [`idatasequence.md`](idatasequence.md), [`idatapipeline.md`](idatapipeline.md),
[`iresettable.md`](iresettable.md).

## Problem

Video devices (`IVideo`, e.g. the DMK 23GP031 fibercamera, typically 2-3k x 2-3k at 1-10 FPS)
deliver a continuous stream. A useful product is often not one frame but N consecutive frames,
either kept as a 3D cube or combined (mean, median, kappa-sigma, ...) into one frame.

`IDataSequence.grab_sequence()` doesn't fit:
- It's fire-and-forget and produces N separate files. A stack is **one** product, and the caller
  wants its filename back, like `grab_data()`.
- `DataSequenceMixin._run_sequence()` loops `grab_data()`. On `BaseVideo`, each `grab_data()`
  waits for a fresh frame and requests FITS headers again, so frames would not be consecutive
  and every frame would cost a full round of header RPCs.

So this is a new interface, not a new version of `IDataSequence`.

## Decision

```python
@dataclass
class DataStackState:
    count_total: int  # 0 when idle / no stack running
    count_left: int
    time: Time = field(default_factory=Time.now)


class IDataStack(IAbortable, metaclass=ABCMeta):
    """The module can grab a stack of consecutive frames (images, ...) into one product."""

    __module__ = "pyobs.interfaces"

    state = DataStackState

    @abstractmethod
    async def grab_stack(self, count: int, broadcast: bool = True, **kwargs: Any) -> str:
        """Grab `count` consecutive frames into one product and return its name.

        Without a pipeline selected (IDataPipeline), the product is a 3D cube of all frames.
        With one, the pipeline runs on the cube (e.g. to combine it) and only its result is
        stored.

        Blocks until the product is stored. Progress is available via DataStackState.

        Args:
            count: Number of frames.
            broadcast: Broadcast existence of the product.

        Returns:
            Name of the stored product.

        Raises:
            InvalidArgumentError: If count < 1, or the stack would exceed the module's memory cap.
            DeviceBusyError: If the device is exposing, or running a sequence or another stack.
            AbortedError: If the stack was aborted.
            GrabImageError: If a frame could not be grabbed, frames don't match, or the
                pipeline failed.
        """
        ...
```

Named `IDataStack` (not `IImageStack`) to sit alongside `IData`/`IDataSequence`. Only images
are implemented now. A stack of 1D spectra would be a 2D array with the same semantics, but
`BaseSpectrograph` is out of scope for the same reason as in
[`idatapipeline.md`](idatapipeline.md): spectra are `HDUList`s, not `Image`s.

Extends `IAbortable` like `IDataSequence`: `abort()` discards the stack.

### Blocking, unlike `grab_sequence()`

`grab_sequence()` returns immediately because its result is N files over time and its timeout
would have to scale with `count` ([`idatasequence.md`](idatasequence.md)). A stack produces one
file that the caller needs, so `grab_stack()` blocks and returns its name, like `grab_data()`.
Its timeout scales with `count`, but it's computed from the same inputs as `grab_data()`'s, so
it stays meaningful (see Timeouts).

### Pipelines

No `pipeline` parameter. The module's currently selected pipeline (`IDataPipeline`) runs on
the cube, exactly as it runs on single frames. Combining is just a pipeline step
(`CombineStack`, next plan), so the stack code never needs to know about combine methods.

Consequence: until `CombineStack` exists, a stack is stored as a raw cube (subject to the
memory cap). Pipelines selected for stacks should start with a combine step. Most existing
processors assume 2D data and will fail or misbehave on a cube. That is accepted, not guarded
against.

## Product format

Raw cube, as written when no pipeline is selected:

- Data: `numpy` shape `(count, ny, nx)`, dtype of the frames (no conversion). FITS axes:
  `NAXIS1 = nx`, `NAXIS2 = ny`, `NAXIS3 = count`.
- Primary header: the **first** frame's full header (all requested FITS headers, driver
  headers), plus:
  - `CTYPE3 = 'FRAME'`: marks axis 3 as a frame axis. Also used by `Image.is_color` (below).
  - `NFRAMES = count`: number of frames in the stack.
  - `DATE-OBS`: start of the first frame (from the first frame's header, unchanged).
  - `DATE-END`: end of the last frame.
  - `EXPTIME`: per-frame exposure time (unchanged meaning).
- Extension `FRAMES`: a binary table with one row per frame: `FRAME` (int, 0-based),
  `DATE-OBS` (str, ISO), `EXPTIME` (float, seconds). Written and read by `Image` (new `frames`
  attribute, below).

All frames must have the same shape and dtype. A mismatch (e.g. someone called `set_window()`
mid-stack) raises `GrabImageError` and stores nothing.

A single frame that is itself 3D (a color frame from a video device) is rejected with
`GrabImageError("Stacking color frames is not supported.")`. Stacking those would need a 4D
array, and nothing downstream handles that.

`count == 1` still produces a 3D cube with `NAXIS3 = 1`, so consumers never have to guess the
layout from `count`.

A future `CombineStack` processor reduces this to 2D, removes `CTYPE3`/`NAXIS3`, keeps
`NFRAMES`, and keeps the `FRAMES` table.

## Required `Image` changes

`pyobs/images/image.py`:

1. **NAXIS for 3D data.** `Image.__init__` sets `NAXIS1 = data.shape[1]`, `NAXIS2 = data.shape[0]`,
   which is wrong for 3D (it puts `ny` into `NAXIS1`). Change to `NAXIS1 = shape[-1]`,
   `NAXIS2 = shape[-2]`, and `NAXIS3 = shape[0]` for 3D. Identical for 2D. This also fixes the
   in-memory header of existing color images (3, ny, nx), which have the same bug today.
   astropy recomputes `NAXISn` on write, so files on disk were never affected.
2. **`is_color` false for cubes.** Currently `len(shape) == 3 and shape[0] == 3`
   (`image.py:655`), so a 3-frame cube counts as RGB and gets mangled by
   `to_grayscale()`, the pillow annotation processors and `SimpleDisk`. Add
   `and self.header.get("CTYPE3") != "FRAME"`.
3. **`frames` table.** New optional `frames: Table | None` constructor argument and property,
   handled like `catalog`: copied in `copy()`, written as a `FRAMES` binary table HDU in
   `writeto()`, read back in `_from_hdu_list()` if a `FRAMES` HDU exists.

`BaseCamera.apply_meridian_flip()` (`basecamera.py`) flips with `image.data[::-1, ::-1]`. On a
cube that flips the frame axis and y, not y and x. Change to `image.data[..., ::-1, ::-1]`,
identical for 2D. (Existing color images have the same bug today.)

## Memory cap

New init parameter on `BaseCamera` and `BaseVideo`: `max_stack_bytes: int = 2 * 1024**3`
(2 GiB). Frames go into a preallocated array, so memory is `count * frame.nbytes` plus whatever
the pipeline allocates (a float32 median roughly doubles it for uint16 frames).

For scale (16-bit frames): 2k x 2k is 8 MB/frame, 3k x 3k is 18 MB/frame, so 2 GiB is
roughly 250 or 115 frames.

Checks:
- **Before the first frame**, if the frame size is known from the last grabbed frame
  (`BaseVideo._last_image.data.nbytes`, `BaseCamera._last_frame_nbytes`, a new attribute set
  after every exposure): `count * nbytes > max_stack_bytes` raises `InvalidArgumentError`
  immediately. Advisory, since settings may have changed since then.
- **After the first frame** (authoritative): same check with the real frame. Raises
  `InvalidArgumentError`, discards the frame, stores nothing.

The cap applies whether or not a pipeline is selected. It's about RAM, not file size.

## Timeouts

`grab_stack()` gets its own `@timeout` function per base class:

- `BaseCamera`: `count * (exposure_time + stack_frame_overhead) + stack_timeout_margin`
- `BaseVideo`: `count * (frame_time + stack_frame_overhead) + stack_timeout_margin`, where
  `frame_time = self._exposure_time` if the driver has one (same `hasattr` check as
  `calc_expose_timeout` in `basevideo.py`), else `1.0`. Plus one extra frame, because the stack
  starts one frame late (see below).

New init parameters (both classes): `stack_frame_overhead: float` (`BaseCamera`: 10.0 s for
readout + transfer, `BaseVideo`: 2.0 s) and `stack_timeout_margin: float = 60.0` (header
requests, cube assembly, pipeline). The margin is what covers a median over a large cube, which
is **not** instantaneous (seconds to tens of seconds for ~2 GB, an estimate, not benchmarked).

## `BaseCamera` implementation

Refactor `__expose()` into two private steps so single grabs and stacks share them:

- `__acquire_frame(exposure_time, open_shutter) -> Image`: the current body from
  `self.expose_abort.clear()` through the flip (exposure, error wrapping, `FLIPX`/`FLIPY`).
  Sets `self._last_frame_nbytes`.
- `__finish_product(image, image_type, header_futures_before, header_futures_after, broadcast, pipeline) -> tuple[Image, str]`:
  `EXTNAME`, `IMAGETYP`, `add_custom_fits_headers`, requested headers, `add_fits_headers`,
  `apply_meridian_flip`, **pipeline**, `format_filename`, upload, broadcast.

`__expose()` then becomes: `_init_exposure()`, request headers before, `__acquire_frame()`,
request headers after, `__finish_product()`. Behavior for single grabs is unchanged.

`grab_stack(count, broadcast)`:

1. Validate `count >= 1`, busy check (`self._camera_status != IDLE`, `self._sequence_count_left > 0`,
   or `self._stack_running`), advisory memory check.
2. Capture `exposure_time`, `image_type`, `pipeline` once. Set `self._stack_running = True`,
   `self._stack_abort = False`, status `EXPOSING`, publish `DataStackState(count, count)`.
3. `_init_exposure()` once. Request FITS headers `before=True` once.
4. For each frame: if `self._stack_abort`: raise `exc.AbortedError`. `__acquire_frame()`.
   First frame: reject 3D frames, authoritative memory check, allocate
   `np.empty((count, *shape), dtype)`, keep its header as the product header. Later frames:
   shape/dtype check. Copy into the cube. Record `DATE-OBS` and exposure time for the `FRAMES`
   table. Publish `DataStackState(count, left)`.
5. Request FITS headers `before=False` once. Build `Image(cube, header=first_header, frames=table)`,
   set `CTYPE3`, `NFRAMES`, `DATE-END`. `__finish_product()`.
6. `finally`: status `IDLE`, `self._stack_running = False`, publish `DataStackState(0, 0)`.

Abort: `abort()` also sets `self._stack_abort = True`. A separate flag is required because
`self.expose_abort` is cleared at the start of every exposure, so an `abort()` that lands between
two frames would otherwise be lost.

`_sequence_busy()` needs no change (status is `EXPOSING` for the whole stack), but add
`self._stack_running` to it for clarity.

`_init_exposure()` is called once per stack, not per frame. It's a setup hook (e.g. pyobs-monet
uses it to apply instrument mode); per-frame calls would be redundant.

## `BaseVideo` implementation

Frames arrive in `_set_image()` (`basevideo.py:663`) at the device's rate. A stack is a request
that `_set_image()` fills:

```python
class StackRequest:
    count: int
    broadcast: bool
    image_type: ImageType
    pipeline: str | None
    header_futures: dict[str, asyncio.Task[Any]] | None  # requested when armed
    date_obs_first: str | None
    cube: NDArray[Any] | None
    dates: list[str]
    done: asyncio.Event
    error: Exception | None
```

Only one stack at a time (`self._stack_request: StackRequest | None`).

Consecutive-frame semantics match `grab_data()`: the request is **armed** on the next frame
(FITS headers requested there, like `NextImage`), and frames are collected from the frame
**after** that. So every collected frame started after `grab_stack()` was called.

In `_set_image()`, after the flip and before the JPEG/live-view part, if a stack request is
active:
- Not yet armed: request FITS headers (`await self.request_fits_headers()`, the same call
  `_set_image()` already makes for `NextImage`), mark armed. This frame is not collected.
- Armed: first collected frame: reject 3D frames (set `error`, set `done`), authoritative memory
  check, allocate the cube. Then `cube[i] = data` (copies, so drivers reusing buffers are safe),
  append `date_obs`, publish `DataStackState` progress **without awaiting anything slow**. When
  full, set `done`.
- Keep this cheap. `_set_image()` runs on the event loop at up to 10 Hz, so no header requests
  after arming, no FITS building, no pipeline here.

`grab_stack()`:
1. Validate, busy check (`self._stack_request is not None`), advisory memory check,
   `await self.activate_camera()`.
2. Create and install the request, publish `DataStackState(count, count)`.
3. Wait on `done`. While waiting, call `activate_camera()` once per second so `_active_update()`
   doesn't put the camera to sleep during a long stack (100 frames at 1 FPS is longer than the
   default `sleep_time` of 60 s).
4. If `error` is set, raise it. If aborted, raise `exc.AbortedError`.
5. Build the `Image` (cube, `DATE-OBS` of the first frame, `IMAGETYP`, `CTYPE3`, `NFRAMES`,
   `DATE-END`, `FRAMES` table), `add_requested_fits_headers()`, `add_fits_headers()`, set
   `DataPipelineName` meta, then `_finish_image(image, broadcast, image_type)`. The pipeline runs
   inside `_finish_image()`, after the pyobs-aravis/pyobs-tis override headers.
6. `finally`: `self._stack_request = None`, publish `DataStackState(0, 0)`.

`BaseVideo` doesn't implement `abort()` today. It gets one (required by `IAbortable`): sets the
stack request's `error = exc.AbortedError(...)` and `done`. Pending single `grab_data()` requests
are not affected.

Single `grab_data()` calls during a stack are allowed. `BaseVideo` already serves concurrent
requests, and a single frame goes through the same selected pipeline.

Note: `BaseVideo._finish_image()` stores the product in the in-memory `DataCache`. A raw cube
therefore sits in memory until evicted (`cache_size`, default 5). With the default 2 GiB cap and
5 cached products, that's up to 10 GiB. Mentioned in the docstring of `max_stack_bytes`, not
fixed here.

## Not in scope

- `CombineStack` processor (mean, median, sum, kappa-sigma via `astropy.stats.sigma_clip`).
  Next plan.
- Stacks within sequences (N stacks of M frames).
- `BaseSpectrograph` stacks.
- Writing large cubes to disk instead of the `BaseVideo` memory cache.
- pyobs-gui support.
