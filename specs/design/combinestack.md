# `CombineStack`: collapse a stack cube into one frame

Status: implemented (2026-09-27), branch `feature/combine-stack`.

Related: [`idatastack.md`](idatastack.md) (the cube format this consumes),
[`idatapipeline.md`](idatapipeline.md) (where it runs). Listed as a follow-up in
[`2026-09-27-data-pipeline-stack-reset.md`](../plans/2026-09-27-data-pipeline-stack-reset.md).

## Problem

`grab_stack()` produces a 3D cube `(count, ny, nx)`. Most users want one combined frame, not
the cube: a raw 2k x 2k x 100 uint16 cube is 800 MB, the combined frame is 16 MB. The stack
code deliberately knows nothing about combining. Combining is a pipeline step, and that step
doesn't exist yet, so today every stack is stored as a raw cube.

## Decision

A new processor package, `pyobs.images.processors.stack`, with one abstract base class and
one concrete class per combine method. Same pattern as `detection/` (`SourceDetection` base,
`DaophotSourceDetection`, `SepSourceDetection`) and `photometry/`.

```
pyobs/images/processors/stack/
    __init__.py         # exports CombineStack and the concrete classes
    combinestack.py     # CombineStack (abstract base)
    mean.py             # MeanStack
    median.py           # MedianStack
    sum.py              # SumStack
    sigmaclip.py        # SigmaClipStack
```

Why classes and not a `method` parameter: each class only takes the parameters it uses
(`sigma`/`maxiters` exist only on `SigmaClipStack`, instead of being silently ignored for other
methods), and new methods (min/max rejection, clipped median, asymmetric clipping) become new
classes instead of new branches.

Each method is its own named pipeline, selected via `set_pipeline()`:

```yaml
pipelines:
  median:
    - class: pyobs.images.processors.stack.MedianStack
  sum:
    - class: pyobs.images.processors.stack.SumStack
      uncertainty: true
  clipped:
    - class: pyobs.images.processors.stack.SigmaClipStack
      sigma: 3.0
```

### `CombineStack` (abstract base)

Does everything that is the same for all methods: input check and pass-through, chunking,
float conversion, NaN handling, the executor call, building the output `Image`, header
changes, and the optional uncertainty and mask.

```python
class CombineStack(ImageProcessor, metaclass=ABCMeta):
    method: ClassVar[str]  # written to COMBMETH, e.g. "median"

    def __init__(
        self,
        uncertainty: bool = False,   # write UNCERT extension
        mask: bool = False,          # write MASK extension
        chunk_bytes: int = 256 * 1024**2,
        **kwargs: Any,
    ): ...

    async def __call__(self, image: Image) -> Image: ...

    @abstractmethod
    def _combine_block(self, block: NDArray[np.float32], need_std: bool) -> BlockResult:
        """Combine one block (count, rows, nx) along axis 0. Runs in the executor."""

    def _exptime(self, exptime: float, total: float) -> float:
        """EXPTIME of the result. Default: per-frame, unchanged."""
        return exptime

    def _add_headers(self, header: fits.Header) -> None:
        """Method-specific headers. Default: none."""
```

`BlockResult` holds, per pixel of the block: `value` (the combined value), `n` (number of
valid values that went into it), and `std` (standard deviation of those values, `ddof=1`, only
computed if `need_std`, i.e. `uncertainty` is on). The base class turns `n` and `std` into uncertainty and mask,
so subclasses only need to report them.

The uncertainty factor differs per method (see below), so it's a class-level hook too:

```python
    @abstractmethod
    def _uncertainty(self, std: NDArray[np.float64], n: NDArray[np.int_]) -> NDArray[np.float64]: ...
```

### Concrete classes

| Class | `method` | `_combine_block` | `_exptime` | `_uncertainty` | Extra params |
|---|---|---|---|---|---|
| `MeanStack` | `mean` | `np.nanmean` | unchanged | `s / sqrt(n)` | none |
| `MedianStack` | `median` | `np.nanmedian` | unchanged | `1.2533 * s / sqrt(n)` | none |
| `SumStack` | `sum` | `np.nansum` | total | `s * sqrt(n)` | none |
| `SigmaClipStack` | `sigmaclip` | `astropy.stats.sigma_clip` (axis 0, centre median), then mean of survivors | unchanged | `s / sqrt(n)` over survivors | `sigma: float = 3.0`, `maxiters: int = 5` |

`SigmaClipStack._add_headers()` writes `COMBSIG = sigma` and `COMBITER = maxiters`.

The median factor 1.2533 is sqrt(pi/2), asymptotic for Gaussian noise. An approximation.

## Input

- **Stack cube** (`ndim == 3` and `CTYPE3 == 'FRAME'`): combined.
- **Anything else** (2D frame, 3D color image without `CTYPE3 = 'FRAME'`): returned unchanged.
  This matters because the selected pipeline runs on single `grab_data()` frames too
  ([`idatapipeline.md`](idatapipeline.md)), so a "median" pipeline has to be harmless on a
  single frame.
- **No data**: log a warning and return the image unchanged (like `Smooth`).

Any mask or uncertainty on the input cube is ignored. Nothing produces those for cubes today.

## Output

- Data: 2D `(ny, nx)`, `float32`, for every method, including `SumStack` on integer frames.
- Header: the cube's header, plus:
  - Removed: `CTYPE3`, `NAXIS3`, and any other axis-3 WCS keys (`CRPIX3`, `CRVAL3`, `CDELT3`,
    `CUNIT3`) if present. `NAXIS` is recomputed by astropy on write.
  - Kept: `NFRAMES`, `DATE-OBS` (start of first frame), `DATE-END` (end of last frame).
  - `COMBMETH = <method>`.
  - `TEXPTIME`: total exposure time, sum of the `FRAMES` table's `EXPTIME` column (fallback
    `NFRAMES * EXPTIME` if there's no table).
  - `EXPTIME`: from `_exptime()`. `SumStack` sets it to `TEXPTIME`, all others keep the
    per-frame value. That keeps counts / `EXPTIME` correct for photometry on the result.
  - Method-specific headers from `_add_headers()`.
- `FRAMES` table: kept unchanged.
- Meta (e.g. `DataPipelineName`): kept.

Keyword names (`COMBMETH`, `COMBSIG`, `COMBITER`, `TEXPTIME`) are a proposal, not an
existing convention in pyobs.

### Optional extensions

Both off by default, so the product stays one 2D frame unless configured. Handled entirely in
the base class.

- **`uncertainty: true`**: `_uncertainty(std, n)` written to `Image.uncertainty` (`UNCERT`
  HDU). `n < 2` gives NaN. This is empirical scatter between frames, not a noise model (no
  gain, read noise, or Poisson term). For static scenes that's what we want. For anything
  varying between frames (seeing, a moving target), it's inflated by that variation.
- **`mask: true`**: `Image.mask` set where `n == 0` (NaN in all frames, or all clipped).
  Written as uint8 `MASK` HDU by the existing `Image.writeto()`.

## NaN handling

After float conversion, subclasses use the NaN-aware functions (`np.nanmean`,
`np.nanmedian`, `np.nansum`). `sigma_clip` masks non-finite values itself (checked with astropy 7.2,
it also logs a warning about it, which the base class suppresses).

Two traps, both handled in the base class so subclasses can't get them wrong:
- `np.nansum` of an all-NaN pixel returns **0**, not NaN. The base class sets `value` to NaN
  wherever `n == 0`, after `_combine_block()`, for every method.
- `np.nanmean`/`np.nanmedian` warn on all-NaN slices ("Mean of empty slice"). The base class
  wraps `_combine_block()` in `warnings.catch_warnings()`, the NaN is the intended result.

`n` is computed by the subclass because only it knows what was clipped. For the plain methods
it's `np.count_nonzero(~np.isnan(block), axis=0)`, a shared helper on the base class.

Integer frames can't contain NaN, so this only matters for drivers delivering float frames.

## Memory and chunking

A 2 GiB uint16 cube (the default `max_stack_bytes`) becomes 4 GiB as float32, and
`sigma_clip` adds a boolean mask plus temporaries on top. So the base class never converts the
whole cube:

- Allocate the output `(ny, nx)` float32 up front (plus uncertainty / mask if enabled).
- Process blocks of rows: `block = cube[:, y0:y1, :].astype(np.float32)`, call
  `_combine_block(block)`, write into `out[y0:y1]`.
- Rows per block: `max(1, chunk_bytes // (count * nx * 4))`, so `chunk_bytes` bounds the float32
  copy of one block. Actual working memory per block is a small multiple of that
  (`SigmaClipStack` roughly 2 to 3x, estimated, not measured).
- Subclasses accumulate in float64 (`dtype=np.float64` on the reduction) and return float64,
  the base class casts to float32. Exception: `np.nanmedian` has no `dtype` argument, so
  `MedianStack` takes the median in float32 (a selection, no accumulation) and casts after. The reduction output is only one block row, so this costs
  nothing noticeable, and it avoids float32 rounding on long sums (float32 represents integers
  exactly only up to 2^24, and 256 saturated uint16 frames already reach that).

**Don't `image.copy()` the input.** That duplicates the cube. Build the result with the
`Image` constructor from the new 2D data, the (copied) header, `frames`, and `image.meta`.

Peak extra memory for a 2 GiB cube with defaults: roughly 16 MB (output) plus a few hundred MB
of block working set, instead of 4 to 8 GB.

## Event loop

The pipeline runs on the event loop ([`idatapipeline.md`](idatapipeline.md)), and a median over
2 GB takes seconds to tens of seconds (estimate, not benchmarked). The base class runs the whole
chunk loop in **one** `loop.run_in_executor(None, ...)` call, not one call per chunk. numpy and
astropy release the GIL for most of the heavy work, so frames and XMPP keep flowing during the
combine. `_combine_block()` therefore runs in a worker thread and must not touch the event loop.

Consequence, same as for any pipeline step: `abort()` can't interrupt a running combine (see
the abort note in [`idatastack.md`](idatastack.md)). Acceptable for now.

## Tests

`tests/images/processors/stack/`:

- `test_combinestack.py`, base class behavior, using a trivial test subclass:
  - 2D input and a 3D color image without `CTYPE3` pass through unchanged.
  - Header: `CTYPE3`/`NAXIS3` gone, `NFRAMES`/`FRAMES` kept, `COMBMETH` set, `TEXPTIME`,
    fallback without `FRAMES` table.
  - Chunking: a tiny `chunk_bytes` forcing many blocks gives the same result as one block. Odd
    row counts, `rows_per_block == 1`.
  - `n == 0` pixels become NaN even if `_combine_block()` returns 0 (the `nansum` trap), and
    are flagged in `mask`.
  - Uncertainty `n < 2` gives NaN.
  - Round trip through `writeto()`/`from_bytes()` with uncertainty and mask.
- `test_methods.py`, per concrete class: result compared to numpy/astropy directly, `EXPTIME` rule,
  uncertainty factor. `SigmaClipStack`: rejects a single outlier frame, `COMBSIG`/`COMBITER`
  set.
- `tests/modules/camera/test_grab_stack.py`: end-to-end `grab_stack()` with `MedianStack`
  (the mean-only stand-in stays for the existing pipeline test).

## Not in scope

- Asymmetric clipping (`sigma_lower`/`sigma_upper`), clipped median, min/max rejection. Each
  would be a new parameter or a new subclass later.
- Frame alignment / shift-and-add. Frames are combined pixel by pixel as grabbed.
- Weighting by exposure time. All frames of a stack are taken with the same requested
  exposure time.
- Noise-model uncertainty (gain, read noise).
- Combining color stacks (4D). `grab_stack()` rejects those already.
