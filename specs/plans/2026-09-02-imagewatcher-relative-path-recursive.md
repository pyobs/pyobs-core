# Plan: ImageWatcher — relative-path preservation and recursive watching

Status: **implemented, PR open** — cleanup-of-empty-dirs (§3) deliberately deferred, see below

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

- [x] Add a `flatten: bool = True` constructor option. Default `True` preserves current behavior
      for every existing user of `ImageWatcher` fleet-wide (no silent semantics change).
- [x] When `False`, the non-templated destination branch in `_worker` preserves subdirectory
      structure between source and destination (implemented via `PurePosixPath.relative_to` +
      join, not the naive `str.replace` originally sketched here — safer against a path
      coincidentally recurring elsewhere in the string). The FITS-header-templated branch is
      unaffected either way — it already builds its own path from header placeholders.

## 2. Recursive watching

`_watch_inotify` currently does one non-recursive `inotify.add_watch(local, Mask.CLOSE_WRITE)`
(`imagewatcher.py:96`), built on `asyncinotify.Inotify`. `asyncinotify` ships two recursive
helpers; which one is available depends on version. `RecursiveInotify` (an `Inotify` subclass with
`add_recursive_watch()`) is newer and not present at the fleet's pinned floor (`>=4.2.1,<5` in
`pyproject.toml` — checked directly against the `4.2.1` sdist, which has it. `RecursiveWatcher`
(an async-generator wrapper around a plain `Inotify`, same file) *is* present at `4.2.1`, so that's
the one to build on without bumping the dependency floor. Both implement the same policy: add
watches on `CREATE`/`MOVED_TO`, drop them on `MOVED_FROM`, and rely on the kernel's automatic
`IGNORED` event to clean up watches on plain deletion (no explicit `rm_watch()` call needed for
that case — `RecursiveWatcher.watch_recursive()`'s own comment: "DELETE event is not
watched/handled here because IGNORED event follows deletion"). This matters concretely: a consumer
like the one motivating this doc deletes-and-recreates one directory before every run (auto-handled
for free) and *renames* a directory into its final location once a run completes (needs the
`MOVED_FROM`/`MOVED_TO` pairing these helpers already implement) — so building on one of them
instead of a hand-rolled watch table avoids re-deriving both cases from scratch.

- [x] Switch `_watch_inotify` to `RecursiveWatcher(Path(local), Mask.CLOSE_WRITE)` +
      `async for event in watcher.watch_recursive():` instead of plain `Inotify` + `add_watch`.
      `watch_recursive()` already filters its yielded events to ones matching the passed-in mask
      (`if event.mask & self._mask: yield event`), so no manual filtering of the internal
      `CREATE`/`MOVED_FROM`/`MOVED_TO`/`IGNORED` bookkeeping events is needed on our side.
- [x] `_watch_poll` needs the equivalent for polling mode: recursive listing instead of a flat
      `vfs.listdir` (`imagewatcher.py:108-123`) — no library helper for this path, since polling
      doesn't go through `asyncinotify` at all. Implemented via `vfs.find(watchpath, pattern)`
      (only `LocalFile` implements `find()` today — other VFS root types raise, so recursive poll
      mode is implicitly local-filesystem-only, same constraint inotify mode already has via
      `vfs.local_path()`). While rewriting this method, also fixed two pre-existing bugs directly
      in the code being touched: `poll_interval` was stored but never actually awaited between
      iterations (a busy-loop), and a stray debug `print()` was left in the new-file branch.
- [x] `open()`'s initial scan (`imagewatcher.py:130-131`, flat `listdir`) needs the same recursive
      treatment, or files present before the module starts get missed. Also switched to
      `vfs.find()`.

### Known limitation (not fixed, not fixable at this layer)

Confirmed by direct reproduction (both a standalone script against `asyncinotify` and a pytest
case, kept as `test_watch_inotify_loses_race_on_rename_into_freshly_created_deep_dir`,
`xfail(strict=True)`): when a *destination* directory tree that doesn't exist yet is created and
something is renamed into it before this process's asyncio loop gets scheduled to consume the
resulting `CREATE` event(s) and add a watch, the move is never observed — inotify only reports
events for already-watched parents, and nothing later re-discovers the miss. This is a genuine
kernel/library-level race, not a bug introduced here; `asyncinotify`'s own example script
documents the same caveat ("doing two changes on a directory before the program has a time to
handle it"). A directory whose parent tree already exists (or existed at watcher startup) is
unaffected — proven by `test_watch_inotify_survives_rename_into_watched_tree`, which passes.

For a consumer whose directories are per-day (e.g. `{year}/{month}/{date}/...`), this means only
the *first* write of a new day/month is at risk (every subsequent `mkdir(exist_ok=True)` into an
already-existing tree is a no-op — no `CREATE` event, no race). If lost, nothing recovers it on
its own. Mitigation belongs at the consumer/deployment level, not in `ImageWatcher` itself — the
standard fix for inotify-based systems is a periodic reconciliation re-scan (re-running the same
recursive `find()` the initial scan/poll mode already does, on some interval, to catch anything
inotify missed). Flagging for whichever downstream plan integrates this so that mitigation gets
scoped explicitly rather than assumed away.

## 3. Cleanup, tests, docs, release

- [ ] Clean up now-empty local subdirectories once their files have all moved (extend
      `cleanup_extra`, or a small periodic sweep) — otherwise a deeply nested watch tree
      accumulates empty directories forever. This is a local-disk/filesystem cleanup concern, not
      an inotify-watch-leak concern — §2 already established that watches for deleted directories
      clean themselves up automatically. Open question: automatic, or is a periodic manual sweep
      acceptable for the first version? **Not implemented in this PR** — deferred, still open.
- [x] Tests: existing flat-mode behavior stays a pure regression (all pre-existing tests still
      pass unmodified); added coverage for recursive watching (new-subdirectory pickup,
      delete-and-recreate, rename-into-an-already-watched-tree, and the known
      rename-into-freshly-created-tree race as an `xfail`), `flatten=False`/`flatten=True` path
      handling (including that the FITS-header-templated branch is unaffected by `flatten`), and
      the `poll_interval` busy-loop fix.
- [x] Docs: `ImageWatcher`'s docstring covers `flatten` and the recursive `pattern` matching;
      Sphinx pulls this in automatically via `autoclass ... :members:`, no separate `.rst` edit
      needed.
- [ ] Release per pyobs-core conventions — not done yet, pending PR review/merge.
