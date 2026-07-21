# Plan: Unify TRIMSEC handling into `Image.trim()` (reconstructed)

*Reconstructed after the fact from `specs/design/image_trim.md` and commit `7e6fc511` — written
after the change landed, not before it.*

## Goal

Replace three independent, drifting TRIMSEC implementations (inline regex in
`ProjectedOffsets`, `fitssec()`, and `Pipeline.trim_ccddata()`) with one `Image.trim()` method
that keeps `data`/`mask`/`uncertainty` aligned, shifts `CRPIX1`/`CRPIX2` to the new origin, and
raises rather than silently invalidating an already-attached catalog. Tracks #342.

## Architecture

`Image.trim()` becomes the single source of truth for trimming. `fitssec()`'s section-string
parser is extracted into a shared `pyobs.utils.fits.parse_section_bounds()`, used by both
`fitssec()` and `Image.trim()`, and now raises a well-defined `ValueError` for a malformed
section keyword instead of failing unpredictably. `Pipeline.trim_ccddata()` is removed outright;
its two call sites trim the `Image` before converting to `CCDData` instead of after.

## File Map

| File | Change |
|---|---|
| `pyobs/images/image.py` | New `Image.trim()` — keeps data/mask/uncertainty aligned, shifts CRPIX1/CRPIX2, raises if a catalog is already attached |
| `pyobs/utils/fits.py` | New shared `parse_section_bounds()`; `fitssec()` now delegates to it |
| `pyobs/utils/pipeline/pipeline.py` | `Pipeline.trim_ccddata()` removed |
| `pyobs/images/processors/calibration/_ccddata_calibrator.py` | Call site updated to trim `Image` before `CCDData` conversion |
| `pyobs/images/processors/offsets/projected.py` | Inline regex TRIMSEC handling replaced with `Image.trim()`/shared parser |
| `docs/source/api/images.rst`, `docs/source/api/utils/fits.rst` | Document the new method and shared parser |
| `tests/images/test_image.py` | New tests for `Image.trim()` |
| `tests/utils/test_fitssec.py` | New tests for `parse_section_bounds()` |
| `CHANGELOG.rst` | Entry for the change |

## Tasks

- [x] Write design doc (`specs/design/image_trim.md`, originally `DESIGN_Image_trim.md`)
- [x] Extract `parse_section_bounds()`, shared by `fitssec()` and the new `Image.trim()`
- [x] Implement `Image.trim()` (data/mask/uncertainty alignment, CRPIX shift, catalog guard)
- [x] Remove `Pipeline.trim_ccddata()`, update its two call sites
- [x] Add tests for both `Image.trim()` and `parse_section_bounds()`
- [x] Update docs and changelog
- [x] Delete design doc on landing (now restored to `specs/design/` instead, per the new
      persistent-design-doc convention)
