# `FileWrittenEvent` from ImageWriter and ImageWatcher

Status: implemented
Date: 2026-10-27
Repos: pyobs-core

## Problem

`ImageWriter` and `ImageWatcher` store files at their final destinations (archive, NAS, ...)
without telling anyone. Other modules that want to act on an archived file (indexing, transfer,
notifications) have to poll the destination.

`NewImageEvent` is not an option: `Pipeline`, `Seeing`, `ScienceFrameAutoGuiding` and
`ImageWriter` itself subscribe to it, so they would reprocess their own output (`ImageWriter` would even loop
on its own event).

## Decisions

- **New event.** `FileWrittenEvent(filename: str)` in `pyobs/events/filewritten.py`, modeled on
  `pyobs/events/newimage.py`: `DataType` TypedDict with only `filename`, `__module__ =
  "pyobs.events"`, `from_dict()` raising `ValueError` if `filename` is missing or not a `str`,
  `filename` property, `__all__`. Not `local` (it goes over XMPP). Payload is only the filename;
  no image type, no source.
- **Filename semantics.** `filename` is the VFS path as written by the sender (e.g.
  `/archive/2026/x.fits`), same convention as `NewImageEvent`. Not a local filesystem path.
  The class docstring says so.
- **ImageWriter.** In `_worker`, send `FileWrittenEvent(output)` only after
  `vfs.write_image(output, img)` returned. Register the event in `open()` (no handler) inside the
  existing `if self._comm is not None:` block, as `pyobs/images/processors/image/save.py` does.
- **ImageWatcher.** In `_process_file`, send `FileWrittenEvent(out_filename)` right after each
  successful destination write, before `process_extra`. One event per destination. New `open()`
  registration guarded by `self._comm is not None` (tests may run without comm), before the
  initial scan.
- **Send errors never fail a write.** Both modules wrap the send in a small helper
  (`_send_file_written(filename)`): skip if `self._comm is None`, `await
  self.comm.send_event(...)`, `except Exception` log a `WARNING` with filename and error and
  return. `CancelledError` still propagates (not an `Exception`).
  - In `ImageWriter`, an escaping exception would currently be swallowed by the outer
    `except Exception: log.error("Could not store image.")` and log a misleading message.
  - In `ImageWatcher`, an escaping exception would go to `_handle_failure`, re-queue the file
    and re-write every destination. So the catch is required there, not cosmetic.
  - Not chosen for now: fire-and-forget `asyncio.create_task`. Avoids blocking the worker but needs task
    bookkeeping and makes ordering/tests harder. See open questions.
- **Known duplicate.** A transient failure in a later destination (or in `process_extra`)
  re-queues the file; the retry re-writes the earlier destinations and re-sends their events.
  Receivers must treat `FileWrittenEvent` as "this file exists now (again)", i.e. be idempotent.
  Documented in the `ImageWatcher` class docstring.

## Implementation checklist

- [x] `pyobs/events/filewritten.py`: `FileWrittenEvent` as above, docstring: "Sent after a file
      has been written to its destination. `filename` is a VFS path."
- [x] `pyobs/events/__init__.py`: import and add `"FileWrittenEvent"` to `__all__`.
- [x] `pyobs/modules/image/imagewriter.py`: import, register in `open()`, add
      `_send_file_written()`, call it after `write_image` in its own statement after the
      `try/except` (only on success, e.g. via `else:`). Class docstring: one sentence on the event.
- [x] `pyobs/modules/image/imagewatcher.py`: import, add `open()` registration, add
      `_send_file_written()`, call it after the `async with ... fd.write(data)` block and before
      `process_extra`. Class docstring: one paragraph on the event, one-per-destination, and the
      duplicate on retry.
- [x] Grep sibling repos for `ImageWatcher`/`ImageWriter` subclasses overriding `open()` without
      calling the base (none found in local checkouts; the iagvt `FileWatcher` mentioned in
      `docs/source/config_examples/iagvt.rst` should be checked where it lives).

## Tests

`tests/test_events.py`:

- [x] `test_file_written_properties`: `FileWrittenEvent("/archive/x.fits").filename`.
- [x] `test_file_written_roundtrip`: `to_json()` -> `EventFactory.from_dict()` gives a
      `FileWrittenEvent` with same filename (same pattern as the `NewImageEvent` round trip).
- [x] `test_file_written_invalid_filename`: `from_dict({"filename": 123})` and `from_dict({})`
      raise `ValueError`.
- [x] Extend the `get_registered_event` check: `get_registered_event("FileWrittenEvent")`.

`tests/modules/image/test_imagewriter.py` (existing `make_writer()`, `DummyComm`, mocked VFS;
replace `writer.comm.send_event` with `AsyncMock`):

- [x] `test_worker_sends_file_written_event`: after a successful write, `send_event` called once
      with a `FileWrittenEvent` whose `filename == "/archive/test.fits"`.
- [x] `test_worker_no_event_on_write_failure`: `write_image` raises, `send_event` not called.
- [x] `test_worker_send_failure_is_logged_not_fatal`: `send_event` raises `RuntimeError`, a
      `WARNING` is logged, no "Could not store image." error, worker keeps processing a second
      queued file.
- [x] `test_open_registers_file_written_event`: `register_event` called with `FileWrittenEvent`
      (no handler) besides the `NewImageEvent` subscription.
- [x] `test_no_send_without_comm`: writer built with `comm=None`, worker writes without error.

`tests/modules/image/test_imagewatcher.py` (existing `make_watcher()`, `make_read_write_ctx()`):

- [x] `test_worker_sends_file_written_event`: one destination, one event with `/dest/<name>`.
- [x] `test_worker_sends_one_event_per_destination`: `destinations=["/a", "/b"]`, two events in
      destination order with the right filenames.
- [x] `test_worker_event_before_process_extra`: record call order via a shared mock; event for
      a destination is sent before `process_extra` for it.
- [x] `test_worker_retry_resends_earlier_destination`: second destination write fails once,
      after the retry `/a` has two events (documents the known duplicate).
- [x] `test_worker_send_failure_does_not_requeue`: `send_event` raises, file is still removed,
      `_retry` empty, nothing re-queued.
- [x] `test_open_registers_file_written_event` and `test_open_without_comm`: `open()` with
      `comm=None` (if `Module.open()` allows it in tests, else test the guarded branch directly).
- [x] Run `uv run pytest tests/test_events.py tests/modules/image`, then
      `uv run pytest tests -m "not integration and not xmpp"`; `ruff check pyobs tests`, `black`
      on changed files, `pyrefly check`. Record results in a Validation section here.

## Docs

- [x] `docs/source/api/events.rst`: `FileWrittenEvent` section with `.. autoclass::`, between
      `ExposureStatusChangedEvent` and `FilterChangedEvent` (alphabetical).
- [x] `docs/source/modules/pyobs.modules.image.rst` uses `autoclass`, so the docstring changes
      above cover ImageWriter/ImageWatcher, including the duplicate-on-retry note. No `specs/`
      links in docs.

## Release

- [x] `CHANGELOG.md` `[Unreleased]` / Added: `FileWrittenEvent`, sent by `ImageWriter` and
      `ImageWatcher` (one per destination) after a successful write.
- [x] Minor release (new public API) via `do-python-release`.

## Risks

- **VFS path, not local path.** Receivers need the same VFS root configured to open the file. A
  watcher destination that is a local-only root (e.g. `LocalFile` on the watcher host) is not
  readable elsewhere. The event says "written", not "fetchable by you".
- **Worker latency.** `XmppComm.send_event` goes through `_safe_send` (5 attempts, 15 s timeout
  each, plus waits), so a stuck pubsub service can block the writer/watcher worker for over a
  minute per file, per destination for the watcher. The file is already safe at that point, but
  the queue stalls.
- **Duplicates on watcher retry** (see Decisions). Also on restart: a file left in `watchpath`
  after a crash between writes is reprocessed and its events re-sent.
- **ImageWriter self-loop is avoided** only because it subscribes to `NewImageEvent`, not
  `FileWrittenEvent`. Keep it that way.

## Open questions

- Fire-and-forget send to avoid the worker stall on a slow pubsub service, or accept the stall?
  Resolved: accept the stall (awaited send). It only happens with an unresponsive pubsub service,
  where the module is broken anyway, and fire-and-forget needs task bookkeeping.
- Should the event name stay generic (`FileWrittenEvent`) while `ImageWriter` only writes FITS?
  Resolved: keep it generic, the watcher copies non-FITS files too.

## Validation

- `pytest tests -m "not integration and not xmpp"`: 2565 passed, 2 failed
  (`tests/mixins/test_datapipeline.py`, both also fail on clean `develop`, unrelated).
- `ruff check`, `black --check`, `pyrefly check`: clean.
- Not done: check the iagvt `FileWatcher` subclass for an `open()` override that skips the base class.
