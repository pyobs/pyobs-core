# Plan: Record pyobs package versions in FITS headers

Status: implemented, closed
Issue: pyobs-core#739 (closed)
Design: `specs/design/package_versions_fits_header.md`
Landed in pyobs-core `b197528c`.

## Problem

No way to reconstruct which versions of pyobs packages were running when a given frame was taken —
see #739 and the design doc for the full discussion (scope, keyword format, caching, keyword-length
check all resolved there). This plan is the concrete implementation checklist.

## Decision (from the design doc)

- Every module implementing `IFitsHeaderBefore`/`IFitsHeaderAfter` writes one `HIERARCH <MODULE>
  VERSION <PYOBS-PACKAGE>` card per loaded pyobs package, no comment (see design doc's keyword-length
  finding — a comment overflows the 80-char card even in the common case since it's redundant with
  the keyword).
- Default package set: `pyobs.utils.versions.loaded_pyobs_packages()` (already exists, added in
  #759), cached once per process rather than rescanned per frame.
- Scope includes `Mastermind` and the test-double modules (`mockweather.py`,
  `_dummytelescopebase.py`, `dummysolartelescope.py`) — no carve-outs.

## Design

### `pyobs/utils/versions.py`

Add, alongside the existing `loaded_pyobs_packages()`:

```python
from collections.abc import Mapping
from pyobs.interfaces import FitsHeaderEntry

_version_cache: dict[str, str] | None = None


def _cached_loaded_pyobs_packages() -> dict[str, str]:
    global _version_cache
    if _version_cache is None:
        _version_cache = loaded_pyobs_packages()
    return _version_cache


def version_fits_headers(
    module_name: str, packages: Mapping[str, str] | None = None
) -> dict[str, FitsHeaderEntry]:
    versions = packages if packages is not None else _cached_loaded_pyobs_packages()
    prefix = module_name.upper()
    return {
        f"HIERARCH {prefix} VERSION {pkg.upper()}": FitsHeaderEntry(ver, "")
        for pkg, ver in versions.items()
    }
```

Check the import: `pyobs.interfaces` imports `..utils.enums`, not `..utils.versions` — no cycle
(already verified in the design doc).

### Wiring

One line added to each implementer's existing header method, merging in
`version_fits_headers(self.name)` (or `module.name` where the method uses `module = cast(Module,
self)`):

- `pyobs/mixins/fitsheader.py`: `FitsHeaderMixin._fitsheadermixin_add_fits_headers`
  (`fitsheader.py:190`) — covers every camera/video/spectrograph module for free, no per-subclass
  change.
- `pyobs/modules/telescope/basetelescope.py`: `BaseTelescope.get_fits_header_before`
  (`basetelescope.py:761`).
- `pyobs/modules/roof/baseroof.py`: `BaseRoof.get_fits_header_before` (`baseroof.py:32`).
- `pyobs/modules/weather/weather.py`: `Weather.get_fits_header_before` (`weather.py:199`).
- `pyobs/modules/pointing/_baseguiding.py`: `BaseGuiding.get_fits_header_before` and
  `get_fits_header_after` (`_baseguiding.py:98,120`).
- `pyobs/modules/robotic/mastermind.py`: `Mastermind.get_fits_header_before`.

Test doubles (`mockweather.py`, `_dummytelescopebase.py`, `dummysolartelescope.py`) need no
separate change — they inherit `get_fits_header_before`/`after` from their real base classes
(`Weather`/`BaseTelescope`), so they pick up the new headers automatically. Verify none of them
overrides the method independently (design doc flagged this as worth checking, not confirmed).

## Testing

- `tests/utils/test_versions.py`: extend with coverage for `_cached_loaded_pyobs_packages()` (cache
  populated once, reused on second call) and `version_fits_headers()` (keyword format, empty
  comment, explicit `packages` override).
- Per touched module (`tests/mixins/test_fitsheader.py`, `tests/modules/telescope/`,
  `tests/modules/roof/`, `tests/modules/weather/`, `tests/modules/pointing/`,
  `tests/modules/robotic/test_mastermind.py`): assert the new `HIERARCH ... VERSION ...` cards
  appear in the returned/written header. Check existing exact-header-dict assertions in these
  tests aren't broken by the new unconditional keys — update them to account for the new cards
  where they compare full dicts rather than checking individual keys.
- Full `.venv/bin/pytest` run to confirm no regressions.

## Out of scope

- Cross-repo consumption of these headers (e.g. an archive/portal UI surfacing them) — not
  requested, not part of #739.
- Non-pyobs vendor SDK versions (e.g. camera driver SDK) — the `packages` override on
  `version_fits_headers()` supports this per-module later if a maintainer wants it, but no driver
  repo is being touched here.

## Open questions

None blocking — design doc resolved scope, keyword format, and the keyword-length concern.

## Implementation checklist

- [x] Add `_cached_loaded_pyobs_packages()` and `version_fits_headers()` to `pyobs/utils/versions.py`.
- [x] Wire `FitsHeaderMixin._fitsheadermixin_add_fits_headers` (`pyobs/mixins/fitsheader.py`).
- [x] Wire `BaseTelescope.get_fits_header_before` (`pyobs/modules/telescope/basetelescope.py`).
- [x] Wire `BaseRoof.get_fits_header_before` (`pyobs/modules/roof/baseroof.py`).
- [x] Wire `Weather.get_fits_header_before` (`pyobs/modules/weather/weather.py`).
- [x] Wire `BaseGuiding.get_fits_header_before`/`get_fits_header_after`
      (`pyobs/modules/pointing/_baseguiding.py`).
- [x] Wire `Mastermind.get_fits_header_before` (`pyobs/modules/robotic/mastermind.py`).
- [x] Confirm the three test-double modules don't override the header method independently; fix if
      any do. **`MockWeather` did** (implements `IFitsHeaderBefore` directly, doesn't subclass
      `Weather`) — wired separately (`pyobs/modules/weather/mockweather.py`).
      `_dummytelescopebase.py`/`dummysolartelescope.py` inherit `BaseTelescope`'s implementation
      unchanged, no separate wiring needed.
- [x] Extend `tests/utils/test_versions.py` for the two new functions.
- [x] Update/extend per-module tests for the new header cards (`tests/mixins/test_fitsheader.py`,
      `tests/modules/telescope/test_basetelescope.py`, `tests/modules/roof/test_baseroof.py`,
      `tests/modules/weather/test_weather.py`, `tests/modules/weather/test_mockweather.py`,
      `tests/modules/pointing/test_autoguiding.py`, new `tests/modules/robotic/test_mastermind.py`).
- [x] Run full `.venv/bin/pytest`; confirm no regressions (1909 passed, 1 pre-existing unrelated
      failure — a `/opt/pyobs/storage` permission error in this dev environment, reproduced
      identically on `develop` before this change).
- [x] Run `ruff`/`black`/`pyrefly` per `CLAUDE.md` tooling section — all clean.
- [x] Update this doc's `Status:` to `implemented` once landed; update
      `specs/design/package_versions_fits_header.md`'s `Status:` to `implemented` too; add both to
      `specs/plans/index.md`/`specs/design/index.md` entries.

## Considered mid-implementation, rejected

A concrete `get_fits_header_before`/`after` on `Module` itself (not inheriting the interface),
called explicitly by each root implementer instead of the free function. See design doc's
"Considered and rejected" section — technically wouldn't have widened RPC scope, but adds
identically-named methods to the base of every module type for no real line-count win, and reads
as "Module implements the interface" when it doesn't. Kept the free function.
