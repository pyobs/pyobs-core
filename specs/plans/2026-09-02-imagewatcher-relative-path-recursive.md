# Plan: ImageWatcher — relative-path preservation and recursive watching

Status: planned

## Context

A downstream consumer needs `ImageWatcher` to relocate a whole nested directory tree (e.g.
`{a}/{b}/{c}/{files...}`) from local staging disk to a network share, preserving structure, so
that data survives an outage of that network share instead of being written to it live. This doc
covers only what changes in `pyobs-core`'s `ImageWatcher` itself, written generically since it's a
shared fleet module and other configs may already depend on its current flat/flatten-to-basename
behavior.

`pyobs/modules/image/imagewatcher.py` already does most of what's needed: watch a directory, copy
each new file to one or more destinations, delete the source only once every destination
succeeded, and re-queue (retry) on a destination write failure — so an outage stalls and retries
rather than dropping anything, with no changes required for that part. Two gaps remain:

## 1. Relative-path preservation

- [ ] Add a `flatten: bool = True` constructor option. Default `True` preserves current behavior
      for every existing user of `ImageWatcher` fleet-wide (no silent semantics change).
- [ ] When `False`, the non-templated destination branch in `_worker` computes `out_filename` via
      `filename.replace(self._watchpath, pattern)` instead of
      `os.path.join(pattern, os.path.basename(filename))` (`imagewatcher.py:198`), preserving
      subdirectory structure between source and destination. The FITS-header-templated branch
      (`imagewatcher.py:190-194`) is unaffected either way — it already builds its own path from
      header placeholders.

## 2. Recursive watching

`_watch_inotify` currently does one non-recursive `inotify.add_watch(local, Mask.CLOSE_WRITE)`
(`imagewatcher.py:96`), built on `asyncinotify.Inotify`. `asyncinotify` (already a dependency, ≥
4.2.1 in-fleet) ships `RecursiveInotify`, a drop-in subclass with `add_recursive_watch()`: it walks
and watches all subdirectories up front, then keeps itself in sync — adds watches on
`CREATE`/`MOVED_TO`, drops them on `MOVED_FROM`, and relies on the kernel's automatic `IGNORED`
event (which its base `Inotify.get()` already handles, `__init__.py:596-598`) to clean up watches
on plain deletion, with no explicit `rm_watch()` call needed for that case. This matters
concretely: a consumer like the one motivating this doc deletes-and-recreates one directory before
every run (auto-handled for free) and *renames* a directory into its final location once a run
completes (needs the `MOVED_FROM`/`MOVED_TO` pairing `RecursiveInotify` already implements) — so
building on it instead of a hand-rolled watch table avoids re-deriving both cases from scratch.

- [ ] Switch `_watch_inotify` to `RecursiveInotify` + `add_recursive_watch(local)` instead of plain
      `Inotify` + `add_watch`. Confirm the `CLOSE_WRITE` mask composes correctly with
      `RecursiveInotify`'s own `_DIR_MASK` (`MOVED_FROM | MOVED_TO | CREATE | IGNORED`) — the
      constructor ORs a passed-in mask with `_DIR_MASK` (`add_recursive_watch`,
      `asyncinotify/__init__.py:703-723`), so this should be additive rather than requiring
      separate bookkeeping.
- [ ] `_watch_poll` needs the equivalent for polling mode: recursive listing instead of a flat
      `vfs.listdir` (`imagewatcher.py:108-123`) — no library helper for this path, since polling
      doesn't go through `asyncinotify` at all.
- [ ] `open()`'s initial scan (`imagewatcher.py:130-131`, flat `listdir`) needs the same recursive
      treatment, or files present before the module starts get missed.

## 3. Cleanup, tests, docs, release

- [ ] Clean up now-empty local subdirectories once their files have all moved (extend
      `cleanup_extra`, or a small periodic sweep) — otherwise a deeply nested watch tree
      accumulates empty directories forever. This is a local-disk/filesystem cleanup concern, not
      an inotify-watch-leak concern — §2 already established that watches for deleted directories
      clean themselves up automatically. Open question: automatic, or is a periodic manual sweep
      acceptable for the first version?
- [ ] Tests: existing flat-mode behavior stays a pure regression; add coverage for recursive
      watching (including delete-and-recreate and rename-into-place, the two patterns identified
      in §2), `flatten=False` path preservation, and confirm retry-on-destination-failure still
      works with both new modes.
- [ ] Docs: update the `ImageWatcher` docstring/Sphinx reference for the new option.
- [ ] Release per pyobs-core conventions.
