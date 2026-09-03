# Package versions in FITS headers

Status: proposed. Tracks #739.

## Problem

Issue #739, as filed: no way to reconstruct which versions of pyobs packages were running when a
given frame was taken, which matters for understanding data processing, WCS solutions, and
troubleshooting retrospectively. Different modules (telescope, camera, dome, filterwheel, ...) can
each depend on different pyobs packages at different versions, so a single monolithic version
string doesn't capture it. The issue leaves open: per-module or global snapshot, one keyword per
package or packed into one, per-frame or per-night, which packages qualify, and the keyword name.

## Existing pieces

- **`pyobs/utils/versions.py::loaded_pyobs_packages()`** (added in #759, `81e13a99`) already does
  the discovery job this issue needs: walks `importlib.metadata.packages_distributions()`, keeps
  only distributions whose top-level import name is present in `sys.modules` and whose
  distribution name starts with `pyobs`, resolves each version via `importlib.metadata.version()`.
  Currently its only caller is `pyobs/application.py:395`, which calls it once at process startup
  to log loaded pyobs package versions for comm-less consumers (e.g. web-admin reading a module's
  log/journal) — the result is logged and discarded, not cached or exposed anywhere else. Known,
  already-documented gap: editable installs (dev checkouts) aren't detected, since
  `packages_distributions()` needs file records that `pip install -e` doesn't populate. Not new to
  this doc.
- **`IFitsHeaderBefore`/`IFitsHeaderAfter`** (`pyobs/interfaces/`) are already implemented by
  exactly the modules that contribute real FITS header data: camera/video/spectrograph modules
  (via `FitsHeaderMixin` and its subclasses, `pyobs/mixins/fitsheader.py`), `BaseTelescope`
  (`pyobs/modules/telescope/basetelescope.py:761`), `BaseRoof`
  (`pyobs/modules/roof/baseroof.py:32`), `Weather` (`pyobs/modules/weather/weather.py:199`),
  `BaseGuiding` (`pyobs/modules/pointing/_baseguiding.py:98,120`), and `Mastermind`
  (`pyobs/modules/robotic/mastermind.py`, see obsnum_fits_header.md). None of the five non-mixin
  classes share a common base for header emission — each hand-writes its own dict literal inside
  `get_fits_header_before`/`get_fits_header_after`.
- **Per-frame RPC fan-out already exists.** `FitsHeaderMixin.request_fits_headers`/
  `add_requested_fits_headers` (`fitsheader.py:72-152`) already queries every
  `IFitsHeaderBefore`/`After` client once per frame and merges the results into the image header.
  Version headers ride this existing path — no new RPC.

## Decisions from discussion

- **Scope**: every module implementing `IFitsHeaderBefore`/`After`, not a new hand-picked category
  ("imaging modules," "hardware modules," ...). This reuses the boundary the codebase already
  draws for "contributes to this frame's header" instead of inventing a second one that duplicates
  it (weather, roof, and guiding modules all implement the interface today; excluding them would
  need a new opt-out mechanism, not just a narrower starting set).
- **Keyword**: `HIERARCH <MODULE> VERSION <PYOBS-PACKAGE> = <version>`, one card per pyobs package
  per module — a module can depend on more than one pyobs package (its own driver plus
  `pyobs-core`), independently versioned. `<PYOBS-PACKAGE>` keeps the `pyobs-` prefix (decided
  against dropping it for brevity).
- **Default package set**: every loaded pyobs-* package (`loaded_pyobs_packages()`), not just the
  module's own driver — overridable per module.
- **Cadence**: emitted every frame, matching the existing per-frame `get_fits_header_before`/`after`
  calls — but package discovery itself is computed once and cached at module start, not rescanned
  per frame (installed/loaded packages don't change during a process's lifetime).

## Proposed design

### Discovery: reuse `loaded_pyobs_packages()`, cache it once per process

`loaded_pyobs_packages()` stays as-is (pure function, tested with an injectable `sys_modules`).
Add a small process-global cache around it for the FITS-header call path, since that path calls it
once per frame rather than once at startup:

```python
_version_cache: dict[str, str] | None = None


def _cached_loaded_pyobs_packages() -> dict[str, str]:
    global _version_cache
    if _version_cache is None:
        _version_cache = loaded_pyobs_packages()
    return _version_cache
```

Process-global rather than per-module-instance: every module in one process sees the same loaded
package set, so there's nothing module-specific to key the cache on. This doesn't touch
`loaded_pyobs_packages()`'s existing signature or test coverage — the cache wrapper is a separate,
new function.

### Header emission: one shared helper, not five copies

Add to the same file:

```python
def version_fits_headers(
    module_name: str, packages: Mapping[str, str] | None = None
) -> dict[str, FitsHeaderEntry]:
    """Build one HIERARCH VERSION card per loaded pyobs package.

    Args:
        module_name: Name of the module contributing these headers (e.g. `self.name`).
        packages: Package name -> version to emit. Defaults to the cached loaded-pyobs-packages
            snapshot; pass an explicit mapping (e.g. merged with a vendor SDK version) to override.
    """
    versions = packages if packages is not None else _cached_loaded_pyobs_packages()
    prefix = module_name.upper()
    return {
        f"HIERARCH {prefix} VERSION {pkg.upper()}": FitsHeaderEntry(ver, "")
        for pkg, ver in versions.items()
    }
```

Needs `FitsHeaderEntry` imported from `pyobs.interfaces` — checked for import cycles:
`pyobs/interfaces/__init__.py` imports `..utils.enums`, not `..utils.versions`, so
`utils/versions.py -> interfaces -> utils/enums` is a DAG, not a cycle.

### Wiring into each implementer

- **`FitsHeaderMixin._fitsheadermixin_add_fits_headers`** (`fitsheader.py:190`) — camera/video/
  spectrograph modules all route through this one method, so adding
  `hdr.update(version_fits_headers(module.name))` here covers every imaging module for free, no
  per-module-subclass change needed.
- **`BaseTelescope.get_fits_header_before`** (`basetelescope.py:761`), **`BaseRoof.get_fits_header_before`**
  (`baseroof.py:32`), **`Weather.get_fits_header_before`** (`weather.py:199`),
  **`BaseGuiding.get_fits_header_before`/`get_fits_header_after`** (`_baseguiding.py:98,120`) —
  each adds one line, `hdr.update(version_fits_headers(self.name))`, to its existing return dict.

### Override point

No new virtual method/extension point needed. `version_fits_headers()` takes an optional
`packages` mapping — a module wanting to add a non-pyobs vendor SDK version (or drop one) merges a
custom dict at the call site, e.g.:

```python
hdr.update(version_fits_headers(self.name, packages={**loaded_pyobs_packages(), "sbig-sdk": sdk_version}))
```

Keeps every implementer's existing hand-written header method as the one place to customize,
consistent with how they already differ from each other today.

## Migration

- `pyobs/utils/versions.py`: add `_cached_loaded_pyobs_packages()` and `version_fits_headers()`;
  import `FitsHeaderEntry` from `pyobs.interfaces` and `Mapping` from `collections.abc`.
- `pyobs/mixins/fitsheader.py`: `_fitsheadermixin_add_fits_headers` (`fitsheader.py:190`) gains the
  version-header update.
- `pyobs/modules/telescope/basetelescope.py`, `pyobs/modules/roof/baseroof.py`,
  `pyobs/modules/weather/weather.py`, `pyobs/modules/pointing/_baseguiding.py`,
  `pyobs/modules/robotic/mastermind.py`: one line each in their `get_fits_header_before`/`after`.
- `tests/utils/test_versions.py`: add coverage for `_cached_loaded_pyobs_packages()` and
  `version_fits_headers()`.
- One test per touched module confirming the new `HIERARCH ... VERSION ...` cards appear; existing
  header-content assertions in those modules' tests may need updating once the new keywords appear
  unconditionally.

## Resolved

- **`Mastermind`** is included under the same "every `IFitsHeaderBefore`/`After` implementer" rule
  as everything else — no carve-out. `mastermind.py`'s `get_fits_header_before` gains the same
  `hdr.update(version_fits_headers(self.name))` line as the others (see Migration).
- **Test-double modules** (`mockweather.py`, `_dummytelescopebase.py`, `dummysolartelescope.py`)
  are in scope too, for header-shape consistency between real and mock modules in tests — they
  pick up version headers automatically once wired through their base classes
  (`BaseTelescope`/`Weather`), no separate change needed unless a test double overrides
  `get_fits_header_before`/`after` independently of its base class.

- **Keyword length checked.** astropy's HIERARCH support has no practical keyword-length limit —
  tested up to 100+ char keywords, all spill cleanly into multi-card `CONTINUE` records with no
  error. Real finding instead: the *comment* silently overflows and gets truncated with a
  `VerifyWarning` even in the common case (`HIERARCH CAMERA1 VERSION PYOBS-SBIG` at 35 chars,
  plus any explanatory comment, already exceeds one 80-char card). Fixed by dropping the comment
  entirely (`FitsHeaderEntry(ver, "")` above) — the keyword is already self-describing
  (`<MODULE> VERSION <PACKAGE>`), unlike other HIERARCH entries in the codebase (e.g.
  `HIERARCH GUIDING RMS`, whose comment adds units/meaning the keyword alone doesn't convey).
