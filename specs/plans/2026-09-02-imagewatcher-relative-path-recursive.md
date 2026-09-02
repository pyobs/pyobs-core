# Plan: ImageWatcher — relative-path preservation and recursive watching

Status: **implemented, merged, released** (PR #860, squash-merged to `develop` as `4eb5553d`;
released as `v2.3.0`) — cleanup-of-empty-dirs (§3) deliberately deferred, see below.

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
- [x] Robustness (caught in review): `watch_recursive()`'s internal `add_watch`/`rm_watch` calls
      can raise `OSError` if a directory vanishes between an event being received and the library
      acting on it — a real possibility under directory churn, not hypothetical. Left unhandled,
      that exits `_watch_inotify` entirely; the module's outer `BackgroundTask` machinery restarts
      it, but repeated churn risks tripping its failure-quit guard. Wrapped the watch loop in
      `while True: try: ... except OSError: log.warning(...)`, so a single vanished directory just
      triggers a fresh `RecursiveWatcher` (full re-walk) locally instead of propagating up.
- [x] `_watch_poll` needs the equivalent for polling mode: recursive listing instead of a flat
      `vfs.listdir` (`imagewatcher.py:108-123`) — no library helper for this path, since polling
      doesn't go through `asyncinotify` at all. Implemented via `vfs.find(watchpath, "*")`, always
      unfiltered (see the pattern-filtering note below) — **correction**: an earlier version of
      this doc claimed "only `LocalFile` implements `find()`, other VFS root types raise"; that's
      wrong. `VFSFile.find` is a concrete base-class method (flat `listdir` + `fnmatch`, not
      recursive), inherited by SSH/SMB/SFTP/TempFile — so a non-local watchpath in poll mode or
      `open()` doesn't raise, it silently stays non-recursive instead. Only `LocalFile.find`
      actually walks (`os.walk`) subdirectories. Recursive poll/`open()` behavior is therefore
      still implicitly local-filesystem-only in effect, just via silent flat fallback rather than
      an error — worth a log warning on a non-recursive `find()` result if this becomes a real
      footgun in practice, not done in this PR. While rewriting `_watch_poll`, also fixed two
      pre-existing bugs directly in the code being touched: `poll_interval` was stored but never
      actually awaited between iterations (a busy-loop), and a stray debug `print()` was left in
      the new-file branch.
- [x] `open()`'s initial scan (`imagewatcher.py:130-131`, flat `listdir`) needs the same recursive
      treatment, or files present before the module starts get missed. Also switched to
      `vfs.find()`.
- [x] Pattern filtering, unified: `_watch_poll`/`open()` originally pre-filtered their `find()` call
      by `pattern` (matched only against each entry's basename, per-directory, by `find`'s own
      `fnmatch.filter`), while inotify mode never pre-filters and relies solely on `add_file`'s
      check against the *full* path. That's a real behavioral divergence (caught in review): a
      pattern like `*2026*` would match a file under a `2026/` subdirectory in inotify mode but not
      in poll/`open()` mode, since the full-path/basename distinction changes what matches. Fixed
      by always calling `find(watchpath, "*")` (no pre-filtering) and letting `add_file`'s existing
      full-path `fnmatch` check be the single point of pattern filtering across all three paths.

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

### Second known limitation: a directory renamed while it still holds a queued file

Caught in review, and distinct from the race above (which is about *destination* directories not
yet watched). `add_file` captures a file's path at event/scan time and queues it; `_worker`
doesn't read that file until `wait_time` later. If the directory holding that file is renamed in
between (recursive watching keeps tracking the directory itself fine — this isn't about missing
the rename), the worker's read at the now-stale captured path fails, and the generic exception
handler in `_worker` just logs and moves on — the file is not re-queued at its new location. Note
also that a *file* itself being renamed into an already-watched directory is never observed
either way, queued or not: `MOVED_TO` on a file isn't `CLOSE_WRITE`, so it was never delivered
here even before this PR — unchanged, pre-existing semantics, not a new gap.

Practical exposure is low if a consumer's workflow only renames a directory once it's done writing
into it and *before* anything has had a chance to be queued from it (e.g. the whole directory is
renamed as one atomic step, then files get *added to* the queue only after settling under their
final name) — the two real-filesystem tests here follow exactly that ordering. Not fixed in this
PR; flagged for whichever downstream plan/deployment integrates this so directory-move timing gets
designed around it rather than assumed safe. The same periodic reconciliation re-scan mitigation
above would also catch anything dropped this way.

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
- [x] Release per pyobs-core conventions — `v2.3.0`.

### Review follow-up (thusser, PR #860)

All non-blocking findings addressed:

1. Pattern-filtering divergence between watch modes — fixed, see the "Pattern filtering, unified"
   item above.
2. `find()`-on-non-local-roots claim was wrong — corrected above.
3. Directory-renamed-while-holding-a-queued-file gap — documented as a second known limitation
   above and in the class docstring; not fixed (same reasoning as the first known limitation).
4. `asyncinotify` `OSError` under directory churn — fixed, see the new checklist item above.
5. Nits: removed the dead `event.path is None` guard in `_watch_inotify` (confirmed unreachable —
   `CLOSE_WRITE` events always carry a path) per this repo's own "don't guard against what can't
   happen" convention; rewrote the poll test that relied on implicit `AsyncMock` `side_effect`
   list exhaustion to terminate via the same explicit sleep-then-cancel pattern every other test
   here uses; documented the `flatten=False` + non-mkdir-destination edge case in the `flatten`
   docstring; §3's empty-dir cleanup deferral needs no change, already tracked as open above.
