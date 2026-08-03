# Plan: Per-step error control in image processing pipelines

Status: implemented
Issues: #693, #328 (previous attempt — nested `ExceptionHandler` wrapper, not merged)

## Problem

`PipelineMixin.run_pipeline()` (in `pyobs/mixins/pipeline.py`) applies every step sequentially,
letting exception propagation do the error control: any step that raises aborts the entire chain.
There is no way for a step's failure to be non-fatal while another stays fatal within the same
pipeline run.

Several processors (most notably `AstrometryDotNet` with its `exceptions: True/False`) already
have their own internal try/except that decides whether to raise or return the image unmodified.
But this is per-processor, not configurable from the pipeline config — the same astrometry step
might need to raise in one pipeline (e.g. a calibration path that must have a valid WCS) while
the identical step needs to pass through unmodified in another (e.g. a quick-look pipeline where
a missing WCS is acceptable).

Previous attempt at a fix was nested `ExceptionHandler` wrapper instances in config (#328).
Pushback was that it moves error handling into config files and adds unnecessary nesting.

## Goal

Add per-step `on_error` control to `PipelineMixin.run_pipeline()`. Every processor can declare,
in its own config, how the pipeline should handle an exception from that step. Default behavior
(raise) is unchanged.

## Considered options

1. **`on_error` kwarg on `ImageProcessor.__init__` + pipeline-level try/except on `ImageError`**
   (the issue's direction): add `on_error: "raise" | "error" | "info" | "ignore"` to the
   processor's base class. The pipeline wraps each step in a try/except for `ImageError` and
   dispatches based on `step.on_error`. Processors define `handle_error(image, error)` to customize
   the error branch (e.g. set a FITS header).

2. **Nested wrapper class (the #328 approach)** — keep the `ExceptionHandler` / `WrapperProcessor`
   approach. Rejected in the issue as too much config noise: a separate config block wrapping the
   actual processor, with `error_header` and `on_error` options on the wrapper rather than the
   step itself.

3. **Global per-pipeline error policy** — one policy for the whole pipeline (e.g.
   `pipeline: on_error: log`). Too coarse: calibration still needs to raise on WCS failure while
   quick-look doesn't.

4. **`@error_policy(...)` decorator on processor `__call__`** — declare error handling at the
   class level, not the config level. Doesn't work: processors are instantiated from config
   dicts, and there's no config-driven way to apply a decorator at runtime.

## Decision

Option 1: `on_error` kwarg with 4 modes and `handle_error()` override point.

### 1. `ImageProcessor` — new methods and kwarg

**File:** `pyobs/images/processor.py`

Add `on_error` kwarg to `__init__` and a new `handle_error` method:

```python
class ImageProcessor(Object, metaclass=ABCMeta):
    VALID_ERROR_MODES = frozenset(("raise", "error", "info", "ignore"))

    def __init__(self, on_error: str = "raise", **kwargs: Any):
        """Init new image processor.

        Args:
            on_error: How to handle exceptions from this step. One of:
                - "raise" (default): re-raise the exception, abort pipeline.
                - "error": call handle_error(), pass its return value downstream.
                - "info": log at INFO level, pass unmodified image downstream.
                - "ignore": silently pass unmodified image downstream.
            **kwargs: Passed to Object.__init__.
        """
        Object.__init__(self, **kwargs)

        self._on_error = on_error

        if self._on_error not in self.VALID_ERROR_MODES:
            raise ValueError(
                f"on_error must be one of {self.VALID_ERROR_MODES}, got '{self._on_error}'"
            )

    @property
    def on_error(self) -> str:
        """The error handling mode for this step."""
        return self._on_error

    async def __call__(self, image: Image) -> Image:
        """Processes an image.

        Args:
            image: Image to process.

        Returns:
            Processed image.
        """
        raise NotImplementedError

    def handle_error(self, image: Image, error: ImageError) -> Image:
        """Handle a processing error.

        Override this method to customize error handling. The default
        implementation re-raises, matching the current "raise on error"
        pipeline behavior.

        Subclasses that currently catch exceptions internally (e.g.
        AstrometryDotNet with ``exceptions=False``) should move that logic
        here and set ``on_error="error"`` in ``__init__`` so the pipeline
        dispatches to this method.

        Args:
            image: The image that caused the error.
            error: The ImageError that was raised.

        Returns:
            The image to pass to the next pipeline step. Return a modified
            image to mark it (e.g. set a FITS header), or return the
            original image unchanged.
        """
        raise error

    async def reset(self) -> None:
        """Resets state of image processor."""
```

`__call__` stays abstract, as today — the base class only adds the error-*handling* hook
(`handle_error`), not an error-*catching* wrapper; the catching happens in the pipeline
(next section). Migration path for processors that currently catch their own errors inside
`__call__` (e.g. `AstrometryDotNet`'s try/except, `SepSourceDetection`'s early-return):

1. Add `handle_error` and `on_error` to the base class (as above).
2. Move each processor's internal error-handling logic into its own `handle_error` override.
3. Remove the internal try/except — let the pipeline's per-step try/except (below) catch and
   dispatch instead.

### 2. `PipelineMixin.run_pipeline()` — wrap each step

**File:** `pyobs/mixins/pipeline.py`

```python
async def run_pipeline(self, image: Image) -> Image:
    """Run the pipeline on the given image.

    Each step is wrapped in try/except for exc.ImageError. The step's
    ``on_error`` setting (default "raise") controls whether the exception
    aborts the pipeline, delegates to ``handle_error()``, logs and passes
    the image through, or is silently ignored.

    Non-ImageError exceptions always propagate.

    Args:
        image: Image to run pipeline on.

    Returns:
        Image after pipeline run.
    """
    import pyobs.utils.exceptions as exc

    for step in self._PipelineMixin__pipeline_steps:
        try:
            image = await step(image)
        except exc.ImageError as e:
            match step.on_error:
                case "raise":
                    raise
                case "error":
                    image = step.handle_error(image, e)
                case "info":
                    log.info(f"Step {type(step).__name__} on {image.path}: {e}")
                case "ignore":
                    pass
        image = image  # (no-ops for info/ignore, handled above)

    return image
```

### 3. `AstrometryDotNet` — migrate to handle_error

**File:** `pyobs/images/processors/astrometry/dotnet.py`

- Add `on_error: str` kwarg to `__init__`, forwarding to `Astrometry.__init__`.
- Keep `exceptions: bool` kwarg for backward compatibility — if set, compute `on_error`:
  - `exceptions=True` → `on_error="raise"` (default, so no change needed)
  - `exceptions=False` → `on_error="error"`
- Remove `_handle_error()` method.
- Move its logic into `handle_error()`.
- Remove the try/except from `__call__` — let the pipeline catch and dispatch.

```python
def __init__(
    self,
    url: str,
    source_count: int = 50,
    radius: float = 3.0,
    timeout: int = 10,
    exceptions: bool | None = None,  # deprecated, used to compute if on_error not set
    on_error: str = "raise",
    **kwargs: Any,
):
    Astrometry.__init__(self, on_error=on_error, **kwargs)
    
    # Backward compat: if 'exceptions' is set but 'on_error' is the default,
    # derive on_error from exceptions.
    if exceptions is not None and on_error == "raise":
        if not exceptions:
            self._on_error = "error"
```

```python
def handle_error(self, image: Image, error: exc.ImageError) -> Image:
    image.header["WCSERR"] = 1
    log.warning(error.message)
    return image

async def __call__(self, image: Image) -> Image:
    return await self._process(image)  # no try/except — let pipeline handle it
```

### 4. Deprecation notes

- `AstrometryDotNet.exceptions`: deprecated. If both `exceptions` and `on_error` are set,
  `on_error` takes precedence. Future release can remove `exceptions`.
- The `on_error` / `handle_error` pattern replaces the ad-hoc try/except-within-`__call__`
  pattern. Other processors that already do error handling internally should be migrated
  similarly over time.

### 5. Tests

**File:** `tests/mixins/test_pipeline_on_error.py` (new)

- Test `run_pipeline` with 3-step pipeline where middle step raises `ImageError`.
  - `on_error="raise"` (default): pipeline aborts, exception propagates.
  - `on_error="error"`: `handle_error` is called, return value continues downstream.
  - `on_error="info"`: warning logged, step's output image skipped, input image passed downstream.
  - `on_error="ignore"`: same as info but no log message.
- Test that non-`ImageError` exceptions always propagate regardless of `on_error`.
- Test that `handle_error`'s return value can modify the image (header changes, attached catalog).
- Test that `handle_error` itself raising re-propagates the exception.
- Test `on_error` validation (invalid string → `ValueError`).
- Test `AstrometryDotNet` backward compat (`exceptions=False` → `on_error="error"`).

## Consequences

- **Good:** Per-step error control from config — one line per pipeline step, no nesting.
- **Good:** Existing behavior is unchanged (default `on_error="raise"` matches current implicit
  behavior).
- **Good:** `handle_error` gives subclasses a single, well-documented override point for
  customizing error behavior (set headers, log, return modified image), replacing the current
  scattered pattern of try/except inside `__call__`.
- **Neutral:** Processors that already handle errors in `__call__` (e.g.
  `AstrometryDotNet`) need migration: their try/except is replaced by moving logic to
  `handle_error` and letting the pipeline catch. This is a small refactor.
- **Neutral:** The `exceptions` parameter on `AstrometryDotNet` becomes deprecated (not removed;
  just noted as legacy).
