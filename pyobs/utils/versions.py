from __future__ import annotations

from collections.abc import Mapping
from importlib.metadata import PackageNotFoundError, packages_distributions, version

from pyobs.interfaces import FitsHeaderEntry


def loaded_pyobs_packages(sys_modules: Mapping[str, object] | None = None) -> dict[str, str]:
    """Return the version of every loaded ``pyobs``-prefixed distribution.

    Builds the top-level import name -> distribution name map from
    :func:`importlib.metadata.packages_distributions`, keeps only the distributions whose
    top-level name is present in ``sys_modules`` and whose name starts with ``pyobs``, and reads
    each version from :func:`importlib.metadata.version`.

    Args:
        sys_modules: Module-name -> module mapping to inspect. Defaults to ``sys.modules``.

    Returns:
        Distribution name -> version, sorted by name. A distribution whose version cannot be
        resolved (``PackageNotFoundError``) is skipped.

    Note:
        Editable installs (``pip install -e`` / ``uv pip install -e``, i.e. a dev checkout)
        typically don't populate the file records that ``packages_distributions()`` needs to
        derive its top-level-name -> distribution mapping, so a package installed that way is
        silently omitted here. Not fixed since the only consumer (pyobsd/web-admin reading the
        module's log/journal) only needs this in production, where installs are non-editable.
    """

    if sys_modules is None:
        import sys

        sys_modules = sys.modules

    loaded: dict[str, str] = {}
    for module_name, dists in packages_distributions().items():
        if module_name not in sys_modules:
            continue
        for dist in dists:
            if not dist.startswith("pyobs"):
                continue
            try:
                loaded[dist] = version(dist)
            except PackageNotFoundError:
                continue

    return dict(sorted(loaded.items()))


_version_cache: dict[str, str] | None = None


def _cached_loaded_pyobs_packages() -> dict[str, str]:
    """Process-global, computed once: every module in one process sees the same loaded packages."""

    global _version_cache
    if _version_cache is None:
        _version_cache = loaded_pyobs_packages()
    return _version_cache


def version_fits_headers(module_name: str, packages: Mapping[str, str] | None = None) -> dict[str, FitsHeaderEntry]:
    """Build one ``HIERARCH <module> VERSION <package>`` header card per pyobs package.

    Args:
        module_name: Name of the module contributing these headers (e.g. ``self.name``).
        packages: Package name -> version to emit. Defaults to the cached loaded-pyobs-packages
            snapshot; pass an explicit mapping (e.g. merged with a vendor SDK version) to override.

    Returns:
        Keyword -> :class:`FitsHeaderEntry`, comment intentionally empty: the keyword
        (``<MODULE> VERSION <PACKAGE>``) is already self-describing, and a comment on top of it
        overflows the 80-char FITS card even for common name lengths.
    """

    versions = packages if packages is not None else _cached_loaded_pyobs_packages()
    prefix = module_name.upper()
    return {f"HIERARCH {prefix} VERSION {pkg.upper()}": FitsHeaderEntry(ver, "") for pkg, ver in versions.items()}


__all__ = ["loaded_pyobs_packages", "version_fits_headers"]
