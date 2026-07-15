# `Image.trim()`: unify the three TRIMSEC implementations

Status: proposed. Tracks #342.

## Problem

Issue #342, as filed: applying `TRIMSEC` to image data is currently implemented inline in
`ProjectedOffsets` and would be a better fit as a method on `Image`. The linked comment sketches
`def trim(self) -> Image`, with two implementation options: write it ourselves, or convert to
`astropy.nddata.CCDData` and use `ccdproc.trim_image` ("easier, but adds a dependency on
`ccdproc`").

Re-checked against current code: still valid, and worse than filed. There are now **three**
independent implementations of the same TRIMSEC-parsing-and-slicing logic, not one:

1. `ProjectedOffsets._process()` (`pyobs/images/processors/offsets/projected.py:161-166`) — regex
   `\[([0-9]+):([0-9]+),([0-9]+):([0-9]+)\]`, manual `data[y0-1:y1, x0-1:x1]` slice. Transient only
   — the trimmed array is used for offset correlation and never written back to the `Image`.
2. `fitssec()` (`pyobs/utils/fits.py:20-49`) — a *different* parser (`sec[1:-1].split(",")`, not
   regex), operates on any object with `.header`/`.data` (duck-typed `Image`), defaults to
   returning the full array untouched if the keyword is absent. Used by
   `FlatFielder._get_image_median()` (`pyobs/robotic/utils/skyflats/flatfielder.py:511`).
3. `Pipeline.trim_ccddata()` (`pyobs/utils/pipeline/pipeline.py:35-47`) — converts to
   `ccdproc.CCDData` and calls `ccdproc.trim_image()`, i.e. the contributor's "option 2". Also the
   only one of the three that cleans up afterward: deletes `TRIMSEC`, `DATASEC`, and `BIASSEC` from
   the header post-trim.

The "would add a dependency" objection from the original comment no longer holds:
`ccdproc>=2.4.3,<3` is already a hard dependency (`pyproject.toml:42`) and already imported
directly in `pipeline.py:9`. That's not a reason to prefer option 2 by default, though — see below.

## Why this isn't a copy-paste unification

Looked at what it would take to just replace all three with a thin `Image.trim()` built on
`to_ccddata()` / `ccdproc.trim_image()` / `from_ccddata()` (option 2, the "easier" path). Two of
`Image`'s own methods make that lossy:

- **`to_ccddata()` (`image.py:371-379`) and `from_ccddata()` (`image.py:212-229`) round-trip only
  `data`, `header`, `mask`, `uncertainty`.** `Image` also carries `catalog`, `raw`, and `meta`
  (constructor: `image.py:140-171`; properties: `image.py:546-580`; correctly preserved by
  `Image`'s own internal copy path, `image.py:302-304`) — none of which survive a CCDData round
  trip. None of the three current call sites happen to touch those fields today, so nobody has hit
  this, but a general-purpose `Image.trim()` is exactly the kind of API a caller would reach for
  *after* running source detection or attaching a raw frame — at which point it would silently
  drop the catalog and raw reference.
- **Nobody adjusts WCS after trimming, and routing through `CCDData` wouldn't fix that either.**
  Trimming shifts the pixel origin, so `CRPIX1`/`CRPIX2` should shift with it — grepped all three
  implementations for `CRPIX`/`.wcs`, zero hits anywhere. `ccdproc.trim_image`'s WCS-aware slicing
  only engages if `CCDData.wcs` is populated; `to_ccddata()` never sets it (only passes the header
  as `meta`), so even the "let ccdproc handle it" option doesn't get correct WCS for free — it has
  to be built deliberately either way.

Given that, and that all three call sites operate on plain 2D `data`/`mask`/`uncertainty` arrays
already, this proposes **option 1** (implement directly on `Image`, no `CCDData` round trip) —
it's not meaningfully more work than option 2 once WCS handling has to be written by hand
regardless, and it avoids inventing a new data-loss trap for `catalog`/`raw`/`meta`.

## Proposed interface

```python
def trim(self) -> Image:
    """Return a copy of this image cropped to its TRIMSEC header, if present.

    If no TRIMSEC is set, returns an unmodified copy. CRPIX1/CRPIX2 are shifted to
    account for the new origin if present. TRIMSEC/DATASEC/BIASSEC are removed from
    the result's header, since none remain valid coordinates into the trimmed data.

    Raises:
        ValueError: If TRIMSEC is malformed, or a catalog is already attached (its
            pixel coordinates would silently go stale against the trimmed frame).
    """
```

- **Slicing**: reuse `fitssec()`'s parser (`fits.py:20-49`) rather than `projected.py`'s regex —
  it's already the more defensive of the two (handles the "keyword absent" case explicitly) and
  is already imported independently elsewhere, so keeping it as the one parser removes a
  duplicate rather than adding a third.
- **Fields sliced**: `data`, `mask`, `uncertainty` — all three are pixel-aligned to `data` today
  (`image.py:167-168`) and must move together.
- **Fields left alone**: `raw` (the pre-calibration frame; trimming is a calibration-adjacent
  operation on `data`, not something `raw` semantically follows) and `meta` (not pixel-geometry
  data, copied through unchanged as `Image`'s own copy path already does).
- **`catalog`**: raise rather than silently invalidate. A source catalog's `x`/`y` columns are
  pixel coordinates into the *current* `data` array; trimming without reprojecting them would
  leave a catalog that quietly points at the wrong pixels. None of the three current call sites
  ever trim a post-detection image, so this isn't a behavior regression for anyone — it converts a
  silent correctness bug into a loud one, which is the outcome actually wanted here. Reprojecting
  the catalog on trim is explicitly out of scope (see "Still open" below).
- **WCS**: if `CRPIX1`/`CRPIX2` are present in the header, shift them by the trim origin
  (`CRPIX1 -= x0`, `CRPIX2 -= y0`, matching the same 1-based/0-based convention `fitssec()` already
  applies to the data slice). This fixes a real, currently-shared bug rather than carrying it
  into the new method; flagged as its own line item in Migration below since it's a behavior
  change relative to all three existing implementations, not a pure refactor.
- **Header cleanup**: delete `TRIMSEC`, `DATASEC`, `BIASSEC` after applying — matching
  `pipeline.py:trim_ccddata`'s existing behavior (the one implementation that already does this),
  and necessary for idempotency (`img.trim().trim()` must be a no-op, not a second, wrong trim).
  `basecamera.py:set_biassec_trimsec()` (`basecamera.py:454-503`) always sets `TRIMSEC`/`DATASEC`
  to the same value together, so treating them as one unit to delete is consistent with how
  they're produced, not an assumption invented here.

## Migration

- `pyobs/utils/fits.py`: `fitssec()` stays — it's the parser `Image.trim()` reuses, and
  `flatfielder.py` uses it for the "trim plus cut to a percentage sub-frame" case that isn't just
  a TRIMSEC crop, so it still has a job independent of `Image.trim()`.
- `ProjectedOffsets._process()` (`projected.py:161-166`): replace the inline regex block with a
  call to the shared parser (or `image.trim().data` if restructuring to operate on a trimmed
  `Image` directly is cleaner there) — removes the second, divergent parser.
- `Pipeline.trim_ccddata()` (`pipeline.py:35-47`) can be deleted outright, not kept as a wrapper.
  Checked both of its two call sites — both already have the source `Image` in scope *before* the
  `to_ccddata()` conversion that currently precedes the trim call, so both become "trim the
  `Image`, then convert," not "convert, then trim the `CCDData`":
  - `Pipeline.combine()` (`pipeline.py:66-71`): `d = image.to_ccddata(); d = Pipeline.trim_ccddata(d)`
    -> `d = image.trim().to_ccddata()`.
  - `_CCDDataCalibrator.__init__`/`_trim_image()` (`_ccddata_calibrator.py:16,36-37`): currently
    stores `self._ccd_data = image.to_ccddata()` in `__init__`, then trims it later in a separate
    `_trim_image()` call. Simplifies to trimming `image` once, up front, before either
    `self._ccd_data` or `self._dark_exp_time`-style header reads happen:
    `self._image = image.trim(); self._ccd_data = self._image.to_ccddata()`, and `_trim_image()`
    goes away as a separate step entirely.
- **Behavior change worth a changelog line**: the new CRPIX-shift on trim is a correctness fix, not
  a no-op refactor — any image that previously kept a (silently wrong) untouched `CRPIX` after
  going through `pipeline.py:trim_ccddata` will now get a shifted one. Confirmed no test currently
  asserts the old (wrong) `CRPIX` value survives trimming — grep `tests/` for `trim` before
  landing, to be safe.

## Still open (not resolved by this doc)

- Reprojecting/filtering a `catalog`'s pixel coordinates to match a trimmed frame, instead of
  raising — deferred; no current caller needs it, and it's a meaningfully separate feature
  (coordinate transform + optional out-of-bounds filtering) from "crop the array."
- Whether `ProjectedOffsets` should be restructured to call `image.trim()` and use the result's
  `.data`, versus just sharing the parser — left as an implementation-time call, not a design
  question; either removes the duplicate regex.
- General non-rectangular masking/trimming (e.g. `CircularMask`, unrelated) is out of scope —
  this is specifically about the `TRIMSEC`/`DATASEC`/`BIASSEC` FITS-header convention.
