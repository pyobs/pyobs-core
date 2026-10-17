# Dedicated exception for an unknown VFS root

Status: implemented in pyobs-core (2026-10-17); pyobs-gui follow-up open
Issue: [pyobs-core#941](https://github.com/pyobs/pyobs-core/issues/941)
Date: 2026-10-17
Repos: pyobs-core, pyobs-gui (follow-up only, pyobs-gui#185)

## Problem

A path whose root is not configured fails differently depending on the entry point:

- `VirtualFileSystem.open_file()` (`pyobs/vfs/vfs.py`, ~line 97) raises a plain
  `ValueError(f"Could not find root {root} for file.")`. The convenience wrappers
  (`read_fits`, `write_fits`, `read_image`, `write_image`, `write_bytes`, `read_csv`,
  `write_csv`, `read_yaml`, `write_yaml`) all go through it.
- `_get_class()` (~line 295) does `self._roots[root]["class"]` and fails with a bare
  `KeyError: 'root'`. It serves `local_path()` directly and `find`, `listdir`, `exists`,
  `remove`, `rmdir` via `_get_method()`.

A path without any root (`split_root()`, `ValueError("No valid path with a root.")`) is a
different case and stays a plain `ValueError`.

pyobs-gui (`pyobs_gui/base.py`, `missing_root_message()`) recognizes the unknown-root case by the
message prefix `"Could not find root"`. A wording change would silently break it.

Side finding: `open_file()` checks `root not in self._roots` and then indexes `self._roots` again;
`local_path()` and the five `_get_method()` users index `self._roots[root]` a second time after
`_get_class()`. `set_roots()` can swap the dict from another thread in between (the GUI calls
`open_file` in an executor), so the second lookup can still hit a bare `KeyError` or use a
different root config than the class was resolved from. The shared helper below fixes this by
reading `self._roots` once.

## Decisions

- **Class and location.** `class UnknownRootError(ValueError)` in `pyobs/vfs/vfs.py`, set
  `__module__ = "pyobs.vfs"` like `VirtualFileSystem`, exported from `pyobs/vfs/__init__.py`
  (eager import next to `VirtualFileSystem`, added to `__all__`). Attributes `root: str` and
  `path: str` (the full path as passed in, before splitting).
  - Rejected: putting it in `pyobs/utils/exceptions.py` as a `PyobsError`. That hierarchy is for
    domain errors and RPC transport; `PyobsError.__init__`/`__str__` (`"<Name> msg"`) would change
    the message and break the prefix match in the currently released pyobs-gui. VFS lookups are
    local (each module has its own VFS); a remote failure still arrives as `UnclassifiedError`
    with `original_type`, same as today's `ValueError`. Revisit only if a remote caller needs to
    react to it by type.
- **Message.** `f"Could not find root {root} for file {path}."` Keeps the `"Could not find root"`
  prefix so pyobs-gui releases before the follow-up still work against the new core.
- **KeyError.** Subclass `ValueError` only, not `KeyError`. Grep of pyobs-core and all sibling
  repos under `/home/husser/code/pyobs/` (29 `except ... KeyError` sites) found none wrapping
  `find`/`listdir`/`exists`/`remove`/`rmdir`/`local_path`/`_get_class`/`_get_method`. A
  `ValueError`+`KeyError` double base would also make `str(e)` quote the message (KeyError's
  `__str__`), which is ugly. Third-party code catching `KeyError` from these five methods would
  break; call it out in the changelog under "Changed".
- **Helper.** One private method `_resolve_root(path) -> tuple[str, str, dict[str, Any]]`
  returning `(root, filename, root_config)`: calls `split_root()`, reads `roots = self._roots`
  once, raises `UnknownRootError(root=..., path=...)` if missing. `open_file()` and
  `_get_class()` use it; `_get_class()`/`_get_method()` return the config instead of the root
  name, and `local_path()` plus the five methods pass `**config` instead of re-indexing
  `self._roots[root]`. All private, so the signature change is internal.

## Implementation checklist

- [x] `pyobs/vfs/vfs.py`: add `UnknownRootError(ValueError)` with `__init__(self, root: str,
      path: str)` storing both and building the message above. Docstring names the attributes.
- [x] `pyobs/vfs/vfs.py`: add `_resolve_root()`; use it in `open_file()` (drop the inline check)
      and `_get_class()`. Change `_get_class()` to return `(klass, filename, config)` and
      `_get_method()` overloads to `(callable, filename, config)`; update `local_path`, `find`,
      `listdir`, `exists`, `remove`, `rmdir` to use the returned config.
- [x] Add `Raises:` sections to the docstrings of `open_file`, `local_path`, `find`, `listdir`,
      `exists`, `remove`, `rmdir` (`UnknownRootError` for an unconfigured root, `ValueError` for
      a path without a root).
- [x] `pyobs/vfs/__init__.py`: import and export `UnknownRootError`; one sentence in the module
      docstring after the roots example.
- [x] Check no other code in `pyobs/` indexes `vfs._roots` directly (`grep -rn "_roots\[" pyobs/`).

## Tests (`tests/vfs/test_vfs.py`)

- [x] `test_unknown_root_open_file_raises_unknown_root_error`: `open_file("/nope/x.fits", "r")`
      raises `UnknownRootError`; `isinstance(e, ValueError)`; `e.root == "nope"`,
      `e.path == "/nope/x.fits"`; `str(e)` starts with `"Could not find root nope"`.
- [x] `test_unknown_root_raises_from_all_entry_points`: parametrized over `read_fits`,
      `write_fits`, `read_image`, `write_image`, `write_bytes`, `read_csv`, `write_csv`,
      `read_yaml`, `write_yaml`, `local_path`, `find`, `listdir`, `exists`, `remove`, `rmdir`,
      each with dummy arguments, all raise `UnknownRootError` (async ones awaited). Assert it is
      not a `KeyError`.
- [x] `test_path_without_root_is_plain_value_error`: `open_file("x.fits", "r")` and
      `exists("x.fits")` raise `ValueError` that is not `UnknownRootError`.
- [x] `test_unknown_root_error_exported`: `from pyobs.vfs import UnknownRootError`.
- [x] `test_set_roots_replaces_roots_and_keeps_defaults` already uses
      `pytest.raises(ValueError, match="old")`; tighten to `UnknownRootError`.
- [x] Known-root behaviour unchanged: existing `test_read_file` and `tests/vfs/test_localfile.py`
      pass; add one `exists`/`listdir` round trip on a `LocalFile` root (`tmp_path`) to cover the
      new config plumbing through `_get_method()`.
- [x] Run `uv run pytest tests/vfs`, then `uv run pytest tests`; `ruff check pyobs/`, `black` on
      changed files, `pyrefly check`. Record results in a Validation section here.

## Docs

- [x] `docs/source/api/vfs.rst`: short "Errors" paragraph under "Reading and writing files":
      unknown root raises `UnknownRootError` (a `ValueError`, with `root`/`path`), path without a
      root raises plain `ValueError`. Add `.. autoexception:: pyobs.vfs.UnknownRootError` to the
      API reference.
- [x] `docs/source/recipes/simulation.rst:114`: update the example to
      `UnknownRootError: Could not find root cache for file /cache/<name>.fits.` (check the real
      traceback text from a run before committing it).

## Release

- [x] `CHANGELOG.md` under `[Unreleased]`:
  - Added: `pyobs.vfs.UnknownRootError` (`ValueError` subclass with `root`/`path`) raised by every
    `VirtualFileSystem` entry point for an unconfigured root (#941).
  - Changed: `local_path`, `find`, `listdir`, `exists`, `remove`, `rmdir` raise
    `UnknownRootError` instead of `KeyError` for an unconfigured root; code catching `KeyError`
    there must catch `ValueError` or `UnknownRootError`.
- [ ] Minor release (new public API), via `do-python-release`, only when Tim asks.

## Validation

- `uv run pytest tests -m "not integration and not xmpp"`: 2552 passed, 26 skipped, 1 xfailed.
- `ruff check pyobs/vfs tests/vfs`, `black`, `pyrefly check`: clean.

## Cross-repo follow-up (pyobs-gui, separate change)

- [ ] After the core release: raise pyobs-gui's `pyobs-core` lower bound (currently `>=2.18.1`)
      to the release that contains this.
- [ ] `pyobs_gui/base.py` `missing_root_message()`: `isinstance(exception, UnknownRootError)`,
      use `exception.root` instead of re-splitting the path, drop the prefix match and update the
      docstring. Callers in `videowidget.py` and `datadisplaywidget.py` stay as they are.
- [ ] `tests/test_missing_vfs_root.py`: build `UnknownRootError` instead of a prefixed
      `ValueError`; keep the "other `ValueError` returns None" case.
- [ ] Tick the open item in pyobs-gui `specs/plans/2026-10-04-settings-dialog.md` step 2 and
      close pyobs-core#941 once both are released.
