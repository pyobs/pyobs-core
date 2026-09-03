from __future__ import annotations

from importlib.metadata import PackageNotFoundError

import pyobs.utils.versions as versions_module
from pyobs.interfaces import FitsHeaderEntry
from pyobs.utils.versions import loaded_pyobs_packages, version_fits_headers


def _fake_modules(*names: str) -> dict[str, object]:
    return {name: object() for name in names}


def test_returns_loaded_pyobs_distributions(monkeypatch) -> None:
    monkeypatch.setattr(
        "pyobs.utils.versions.packages_distributions",
        lambda: {"pyobs": ["pyobs-core"], "pyobs_fli": ["pyobs-fli"]},
    )
    monkeypatch.setattr(
        "pyobs.utils.versions.version",
        lambda dist: {"pyobs-core": "2.0.0.dev76", "pyobs-fli": "2.0.0.dev7"}[dist],
    )

    result = loaded_pyobs_packages(_fake_modules("pyobs", "pyobs_fli"))

    assert result == {"pyobs-core": "2.0.0.dev76", "pyobs-fli": "2.0.0.dev7"}


def test_excludes_non_pyobs_distributions(monkeypatch) -> None:
    monkeypatch.setattr(
        "pyobs.utils.versions.packages_distributions",
        lambda: {"numpy": ["numpy"], "pyobs": ["pyobs-core"]},
    )
    monkeypatch.setattr("pyobs.utils.versions.version", lambda dist: "1.0")

    result = loaded_pyobs_packages(_fake_modules("numpy", "pyobs"))

    assert result == {"pyobs-core": "1.0"}


def test_excludes_not_loaded_top_level_names(monkeypatch) -> None:
    monkeypatch.setattr(
        "pyobs.utils.versions.packages_distributions",
        lambda: {"pyobs": ["pyobs-core"], "pyobs_fli": ["pyobs-fli"]},
    )
    monkeypatch.setattr("pyobs.utils.versions.version", lambda dist: "1.0")

    result = loaded_pyobs_packages(_fake_modules("pyobs"))

    assert result == {"pyobs-core": "1.0"}


def test_skips_package_not_found(monkeypatch) -> None:
    monkeypatch.setattr(
        "pyobs.utils.versions.packages_distributions",
        lambda: {"pyobs": ["pyobs-core", "pyobs-missing"]},
    )

    def fake_version(dist: str) -> str:
        if dist == "pyobs-missing":
            raise PackageNotFoundError(dist)
        return "1.0"

    monkeypatch.setattr("pyobs.utils.versions.version", fake_version)

    result = loaded_pyobs_packages(_fake_modules("pyobs"))

    assert result == {"pyobs-core": "1.0"}


def test_sorted_by_name(monkeypatch) -> None:
    monkeypatch.setattr(
        "pyobs.utils.versions.packages_distributions",
        lambda: {"pyobs_fli": ["pyobs-fli"], "pyobs": ["pyobs-core"]},
    )
    monkeypatch.setattr("pyobs.utils.versions.version", lambda dist: "1.0")

    result = loaded_pyobs_packages(_fake_modules("pyobs", "pyobs_fli"))

    assert list(result) == ["pyobs-core", "pyobs-fli"]


def test_defaults_to_sys_modules(monkeypatch) -> None:
    monkeypatch.setattr(
        "pyobs.utils.versions.packages_distributions",
        lambda: {"pyobs": ["pyobs-core"]},
    )
    monkeypatch.setattr("pyobs.utils.versions.version", lambda dist: "1.0")

    result = loaded_pyobs_packages()

    assert result == {"pyobs-core": "1.0"}


def test_version_fits_headers_builds_hierarch_cards() -> None:
    result = version_fits_headers("camera1", {"pyobs-core": "2.4.1", "pyobs-sbig": "1.4.0"})

    assert result == {
        "HIERARCH CAMERA1 VERSION PYOBS-CORE": FitsHeaderEntry("2.4.1", ""),
        "HIERARCH CAMERA1 VERSION PYOBS-SBIG": FitsHeaderEntry("1.4.0", ""),
    }


def test_version_fits_headers_uppercases_module_and_package() -> None:
    result = version_fits_headers("telescope1", {"pyobs-core": "2.4.1"})

    assert "HIERARCH TELESCOPE1 VERSION PYOBS-CORE" in result


def test_version_fits_headers_defaults_to_cached_loaded_packages(monkeypatch) -> None:
    monkeypatch.setattr(versions_module, "_version_cache", None)
    monkeypatch.setattr(versions_module, "loaded_pyobs_packages", lambda: {"pyobs-core": "1.0"})

    result = version_fits_headers("camera1")

    assert result == {"HIERARCH CAMERA1 VERSION PYOBS-CORE": FitsHeaderEntry("1.0", "")}


def test_cached_loaded_pyobs_packages_computed_once(monkeypatch) -> None:
    monkeypatch.setattr(versions_module, "_version_cache", None)
    calls = []

    def fake_loaded_pyobs_packages() -> dict[str, str]:
        calls.append(1)
        return {"pyobs-core": "1.0"}

    monkeypatch.setattr(versions_module, "loaded_pyobs_packages", fake_loaded_pyobs_packages)

    first = versions_module._cached_loaded_pyobs_packages()
    second = versions_module._cached_loaded_pyobs_packages()

    assert first == second == {"pyobs-core": "1.0"}
    assert len(calls) == 1
