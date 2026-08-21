# Plan: Stop ImageWatcher per-file processing from blocking the event loop

Status: proposed
Issues: found via live incident diagnosis on MONET South (`(imagewatcher) module.py:205/207
"Event loop stalled for 0.81s"` / `"...recovered after being stalled for 2.81s total."`,
2026-08-20, on a stock `pyobs.modules.image.ImageWatcher` — config `pyobs-monet/config/south/monet/imagewatcher.yaml`)

## Problem

`ImageWatcher._worker` (`pyobs/modules/image/imagewatcher.py:149-223`) processes every watched
file with several synchronous, never-yielding operations running directly on the module's single
event loop:

1. **`fits.HDUList.fromstring(data)`** (`imagewatcher.py:171`) — a synchronous, CPU-bound astropy
   parse of the entire FITS file, once per file. This is the same class of bug documented for the
   scheduler (`specs/plans/scheduler-event-loop-blocking.md`): `async def` code doing real
   synchronous work on the loop.
2. **`LocalFile.read` / `LocalFile.write` / `LocalFile.close` / `LocalFile.remove`**
   (`pyobs/vfs/localfile.py:48-63, 131-150`) — declared `async def` but execute plain blocking
   syscalls (`fd.read()`, `fd.write()`, `os.remove`) with no executor. The watch-path half of this
   pipeline (`/temp/` → `LocalFile` on `/opt/pyobs/data/new`) hits read on every file and remove
   after every successful store; any write destination that is itself a `LocalFile` hits write.
   Notably, `LocalFile.listdir` *already* offloads via `loop.run_in_executor`
   (`localfile.py:100-101`) — read/write/remove just never got the same treatment. `find`
   (`os.walk`) and `exists` are the same shape (`localfile.py:125-128, 152-168`).
3. The **archive destination is genuinely async** (`ArchiveFile`/`HttpFile` are all `aiohttp`,
   `pyobs/vfs/archivefile.py`, `pyobs/vfs/httpfile.py`) — it does **not** freeze the loop, but it
   dominates wall-clock time per file (in the incident log, `Storing file as …` → `Removing file
   …` gaps of 2–3 s, one file ~10 s). That latency is what eats the queue margin; when the archive
   is slow the worker falls behind the 10 s cadence and the queue grows — a separate pressure from
   the loop freeze, addressed in Non-goals.

The module's own lag watchdog (`_watch_event_loop_lag`, `pyobs/modules/module.py:183-209`,
thresholds `_LOOP_LAG_WARN_THRESHOLD = 0.5` at `module.py:181`) measured a 2.81 s freeze. During
that window the module cannot process inotify events, answer peers' RPCs, or keep its XMPP
keepalive alive (the failure mode ADR 0009 exists to surface early). Per ADR 0009's own
"Consequences", the watchdog reports *that* the loop stalled and roughly *how long* — never
*which* call; the exact culprit still needs one confirm-and-measure pass (see step 0 below).

## Goal

Make `ImageWatcher`'s per-file processing stop blocking the event loop: the FITS parse and the
`LocalFile` I/O it relies on must leave the loop thread, matching the established offload pattern
in this codebase (`LocalFile.listdir`, `VirtualFileSystem.write_fits`'s `asyncio.to_thread`,
the scheduler's `run_cpu_bound`). Fix the `LocalFile` side at the VFS layer — every module that
reads/writes local files through VFS inherits the fix, not just the imagewatcher.

## Considered options

**Offload granularity:**

1. **Offload only the FITS parse in `_worker`.** Smallest diff, targets the most CPU-heavy call
   per file. Rejected as the *only* change: it leaves `LocalFile.read/write/remove` blocking on the
   loop, so a slow/network-mounted watch path still freezes the module, and every other VFS user
   keeps the same latent bug.
2. **Offload the FITS parse *and* make `LocalFile`'s sync methods executor-based** (read/write/
   close/remove/exists/find, mirroring `listdir`). Fixes the class of bug at the layer where it
   lives; benefits all VFS consumers; matches existing precedent. **Chosen.**
3. **Run the whole per-file pipeline in a subprocess**, following `AstroplanScheduler`'s precedent.
   Rejected: the worker needs the live VFS/comm objects (archive upload, `process_extra` hooks);
   serialization overhead per file is disproportionate for what is, per call, bounded work.

**Parallelism (orthogonal):** processing several files concurrently (semaphore-gated) would
reduce the wall-clock backlog but does nothing for the loop freeze, and changes upload-order
semantics — explicitly out of scope (see Non-goals).

## Decision

### 1. Offload the FITS parse — `pyobs/modules/image/imagewatcher.py`

In `_worker`, wrap the parse in `asyncio.to_thread`:

```python
# better safe than sorry
try:
    # get file data
    async with self.vfs.open_file(filename, "rb") as fd:
        data = await fd.read()

    # try to load as fits file; data may well not be a FITS file at all
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", fits.verify.VerifyWarning)
            fits_file = await asyncio.to_thread(fits.HDUList.fromstring, data)
    except Exception:
        fits_file = None
```

`HDUList.fromstring` on already-downloaded bytes is network-free (no IERS auto-download — that
stall shape, `specs/steering/astropy-iers-event-loop-stalls.md`, comes from *time conversions*,
which header parsing does not trigger), so it is safe to run off the loop. The offloaded unit is
one bounded synchronous call per `await`, the exact shape the scheduler plan and
`pysep.py`/`daophot.py`/`aperture_photometry.py` use.

### 2. Make `LocalFile` I/O non-blocking — `pyobs/vfs/localfile.py`

Route the synchronous bodies through the default executor, mirroring the existing `listdir`
(`localfile.py:100-101`):

```python
async def read(self, n: int = -1) -> str | bytes:
    if self.fd is None:
        raise OSError
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, self.fd.read, n)

async def write(self, s: str | bytes) -> None:
    if self.fd is None:
        raise OSError
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, self.fd.write, s)

async def close(self) -> None:
    if self.fd:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self.fd.close)
```

Same treatment for the class-level sync methods: `remove` (`os.remove`), `exists`
(`os.path.exists`), and `find` (`os.walk` — potentially slow on large trees). Extract the sync
bodies into module-level helpers so the executor call stays a plain function.

**Concurrency safety:** each `LocalFile` instance is created per `open_file()` call and used by
exactly one coroutine inside a single `async with` block, so per-instance `fd` calls are strictly
sequential — no locking needed, no shared-state hazard. The default executor's pool is shared, but
each call is short-lived and independent. This matches the documented invariant for the scheduler's
dedicated executor: no shared mutable cache here, so the shared pool is fine.

**Residual (documented, not fixed):** `LocalFile.__init__` still opens the file synchronously
(`open()`, `os.makedirs`, `localfile.py:38-46`). That's milliseconds on local disk; making the
constructor async would break `VirtualFileSystem.open_file`'s sync signature — a breaking VFS API
change not worth it for this plan.

### 3. (step 0, diagnostic) Confirm the culprit and measure before/after

Before deploying the fix, capture ground truth during a stall at the site, per ADR 0009's guidance
(`loop.set_debug(True)` / `slow_callback_duration`, or a `py-spy dump` armed on a stall). The
2026-08-05 scheduler follow-up warns: the last time the cause was guessed from log timing alone,
the guess was wrong, and only a live capture found it. This step both validates that the fix
targets the real call and gives a before/after stall measurement. The code changes below are
correct regardless, but the measurement is what closes the incident properly.

## Tests

### Existing coverage (regression net, must keep passing)

- `tests/vfs/test_localfile.py` — read/write/remove/create-dir semantics are already asserted;
  the executor change is behavior-preserving, this suite catches any value regression.
- `tests/modules/image/test_imagewatcher.py` — worker copy/delete/format/requeue behavior with a
  mocked VFS; unchanged by the offload.

### New tests required

- `tests/modules/image/test_imagewatcher.py`: loop-responsiveness test in the scheduler-plan
  shape — monkeypatch `pyobs.modules.image.imagewatcher.fits.HDUList.fromstring` with a wrapper
  that `time.sleep(0.2)`s (simulating a slow parse; in the buggy path the sleep runs on the loop
  thread and starves everything; offloaded, the thread releases the GIL and the loop keeps
  ticking), run `_worker` on one queued file concurrently with a 10 ms heartbeat via
  `asyncio.gather`, and assert the heartbeat kept ticking on schedule (missed a bounded number of
  beats, far below what a 0.2 s block would cause). This proves the offload actually keeps the
  loop responsive, not just that values still round-trip.
- `tests/vfs/test_localfile.py`: same heartbeat shape against `LocalFile` — monkeypatch the
  instance's `fd` with a fake whose `write`/`read` sleeps (deterministic, no reliance on disk
  speed), assert a concurrent heartbeat keeps ticking while `await f.write(...)` / `await f.read()`
  run. Guards the `LocalFile` half directly.
- Full suite for the touched areas: `pytest tests/modules/image/ tests/vfs/`; `pyrefly` on
  `imagewatcher.py` and `localfile.py` ([[feedback_use_pyrefly_not_mypy]]).

## Consequences

- **Good:** the imagewatcher's event loop stays responsive during file processing — the specific
  symptom in the incident goes away. RPC replies, inotify handling, and comm keepalive are no
  longer frozen for seconds at a time.
- **Good:** the `LocalFile` fix lives at the VFS layer, so every module doing local-file I/O
  through VFS inherits it, not just the imagewatcher — the same systemic argument that justified
  `listdir`'s executor use.
- **Good:** matches the codebase's established "offload one bounded sync unit per `await`"
  pattern rather than inventing a new shape.
- **Neutral:** the FITS parse still runs in a worker *thread*, which shares the GIL with the loop
  thread — pure-Python header parsing can still contend briefly (the 2026-08-05 scheduler
  follow-up's caveat). numpy array work inside `fromstring` releases the GIL, so most of the
  parse is contention-free; the loop stays responsive either way, which is the goal. Process
  isolation is explicitly not pursued here (the worker needs live VFS/comm).
- **Residual:** `LocalFile.__init__`'s sync `open()`/`mkdir` stays on the loop (fast on local
  disk; async constructor would break the VFS API). Also `process_extra`/`cleanup_extra` subclass
  hooks run on the loop — worth a docstring note that these must not block (subclass contract,
  not enforced here).
- **Out of scope, flagged for follow-up:** archive upload latency and queue backlog. The
  `aiohttp` upload is already async and never freezes the loop; if the backlog becomes the
  operational problem (slow archive, 2–10 s/file), the follow-up is bounded concurrency in the
  worker, not more offloading.

## Implementation checklist

- [ ] Step 0: at the affected site, capture the exact blocking call once (asyncio debug or
      `py-spy`) — confirm FITS parse and/or `LocalFile` I/O, record baseline stall duration
- [ ] `imagewatcher.py`: offload `fits.HDUList.fromstring(data)` via `asyncio.to_thread` in
      `_worker`
- [ ] `localfile.py`: route `read`, `write`, `close` bodies through `run_in_executor`
- [ ] `localfile.py`: route `remove`, `exists`, `find` through `run_in_executor` (sync bodies
      extracted as module-level helpers)
- [ ] Docstring note on `ImageWatcher.process_extra`/`cleanup_extra`: subclass hooks run on the
      event loop and must not block
- [ ] New heartbeat-style tests in `tests/modules/image/test_imagewatcher.py` and
      `tests/vfs/test_localfile.py` (per Tests above)
- [ ] `pytest tests/modules/image/ tests/vfs/` green; `pyrefly` clean on both touched files
- [ ] Deploy to site; confirm `module.py:205/207` stall warnings gone (or below threshold) over
      one night
- [ ] Update this doc's `Status:` to `implemented` once landed and verified
