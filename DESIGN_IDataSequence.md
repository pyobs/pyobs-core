# `IDataSequence`: server-side counted data sequences

Status: implemented on `develop`. Tracks #548.

Implementation: `pyobs/interfaces/IDataSequence.py` (interface + `DataSequenceState`),
`pyobs/modules/camera/basecamera.py` (`BaseCamera.grab_sequence`/`abort_sequence`/`_run_sequence`,
and the one-line extension to `abort()`). Tests: `tests/modules/camera/test_grab_sequence.py`.

## Problem

Taking a sequence of N images currently has no server-side concept at all — `ICamera`/`IExposure`
only expose single-shot `grab_data()`. Anything that wants "take N images" today has to drive a
client-side loop, awaiting each exposure before triggering the next. This already happens in
practice: `pyobs-gui`'s `CameraWidget.expose()` does exactly this —

```python
self.exposures_left = self.spinCount.value()
while self.exposures_left > 0:
    await self.datadisplay.grab_data(broadcast)
    self.exposures_left -= 1
```

Consequences of that:
- The sequence lives and dies with the calling client's connection — if the GUI closes or the
  connection drops mid-sequence, the sequence just stops.
- N RPC round-trips instead of one.
- "Abort sequence" is a client-side-only concept today, and it's actually two different operations
  already distinguished in `camerawidget.py`'s `abort()`: if more than one exposure remains, it
  just zeroes `exposures_left` locally (the *running* exposure keeps going to completion, only
  future ones in the loop are skipped); if it's the last exposure, it calls the real
  `proxy.abort()` (hard-stops the running exposure immediately). Neither variant was a real
  server-side operation before this -- `BaseCamera.abort()`'s own docstring already said "Aborts
  the current exposure and **sequence**", which was aspirational until this implementation.

Moving the count into the module itself fixes all three: the sequence survives a client
disconnect, driving it is one RPC call, and abort becomes a real, single, server-side operation.

## Why `IDataSequence`, not `IImageCount`

`grab_data()` — the method this whole design mirrors — doesn't actually live on `ICamera`. It
lives on `IData` (`pyobs/interfaces/IData.py`), a device-agnostic interface already shared by
`ICamera`, `IVideo`, and `ISpectrograph` ("grab_data grabs and returns an image from *whatever
device*"). A spectrograph wanting a counted sequence of spectra is just as legitimate a case as a
camera wanting a counted sequence of images — `pyobs-gui`'s `DataDisplayWidget` already handles
both `NewImageEvent` and `NewSpectrumEvent` for exactly this reason. `IDataSequence` pairs with
`IData` the same way `grab_sequence()` pairs with `grab_data()`, and doesn't bake in an
image-specific assumption the underlying mechanism never actually had.

## Proposed interface

Follows the existing `state`-dataclass + `@abstractmethod` pattern used throughout
`pyobs.interfaces` (e.g. `IExposure`/`ExposureState`, `IMode`/`ModeState`), and pushes state via
`comm.set_state()` rather than exposing a `get_*` RPC getter — matching the reactive-state
convention the rest of `ICamera`'s state (`ExposureState`, `ExposureTimeState`) already follows,
and that the GUI layer was itself migrated onto (`subscribe_state`, not polling).

```python
@dataclass
class DataSequenceState:
    count_total: int  # 0 when idle / no sequence running
    count_left: int
    time: Time = field(default_factory=Time.now)


class IDataSequence(IAbortable, metaclass=ABCMeta):
    """The module can grab a counted sequence of data (images, spectra, ...)."""

    state = DataSequenceState

    @abstractmethod
    async def grab_sequence(self, count: int, broadcast: bool = True, **kwargs: Any) -> None:
        """Start a sequence of `count` grabs. Returns immediately; progress is
        available via the pushed DataSequenceState, and the sequence stops early if
        the device isn't idle when the next grab in the sequence would start.

        Named to match grab_data() -- both are the action-triggering call, unlike the
        passive set_*() config methods (set_exposure_time(), set_image_type(), ...) that
        only ever store a value for the next grab.

        Args:
            count: Number of grabs to take.
            broadcast: Broadcast existence of each grab.

        Raises:
            GrabImageError: If the device is already busy (exposing or already running a
                sequence), or if a grab fails partway through the sequence.
        """
        ...

    @abstractmethod
    async def abort_sequence(self, **kwargs: Any) -> None:
        """Stop the sequence after the current grab. The grab currently in progress, if any,
        finishes normally; no further grabs in the sequence are started.

        This is the graceful counterpart to IAbortable.abort(), which remains the hard-stop
        path: it cancels the running grab immediately *and* the remaining sequence count.
        """
        ...
```

Extends `IAbortable` rather than baking directly into `ICamera`/`IExposure`/`IData` — a device
that doesn't support counted sequences shouldn't be forced to implement this, consistent with the
"small interfaces, compose them" approach already used elsewhere (`ICamera = IData + IExposure`).

Two distinct abort paths, matching the two behaviors `camerawidget.py` already distinguishes
client-side today, now made real server-side operations instead of one being a client-only
`exposures_left = 0` and the other an RPC call:
- `abort_sequence()` (new, `IDataSequence`-specific): soft stop. Current grab finishes
  normally; `count_left` is cleared so no further grabs are started.
- `abort()` (existing, `IAbortable`): hard stop. Cancels the running grab immediately
  (already implemented by `BaseCamera` via `expose_abort`) *and* clears the remaining sequence
  count — the "stop everything now" path.

Note: `BaseCamera` already implements `abort()` (its docstring already says "Aborts the current
exposure and sequence") but doesn't currently declare `IAbortable` as a base class — `ICamera`/
`IExposure` don't extend it either. `IDataSequence(IAbortable)` would mean formally adding
`IAbortable` to `BaseCamera`'s bases too, which is a small, correct side-fix (the method's already
there, this just declares it), not a new requirement being invented.

## Key design call: fire-and-forget, not a blocking RPC

`grab_sequence()` must return immediately and run the sequence as a background task internally
(`asyncio.create_task`, similar to how `BaseCamera` already gates a single exposure with
`self.expose_abort: asyncio.Event`), *not* block until all N grabs are done. This is also why it
can't just be an overload of `grab_data()` itself: `grab_data()`'s contract is a blocking call
that returns the one filename it took, which doesn't fit "returns immediately, N filenames appear
over time via NewImageEvent/NewSpectrumEvent."

This isn't the same failure mode as #664/#666 — those went through `_safe_send()`/XEP-0060 pubsub,
a completely different code path from RPC calls (`Comm.execute()` → `rpc.py`'s XEP-0009 `_rpc.call()`),
and slixmpp already dispatches every incoming RPC handler via `asyncio.ensure_future()`
independently of the connection that delivered it (`xmlstream.py:event()`) — so even a blocking
`grab_sequence()` would keep running server-side regardless of whether the calling client stays
connected. The actual reason to keep it non-blocking is `grab_data()`'s own `@timeout` mechanism:
it exists as a sanity check ("if this takes longer than expected, something is wrong"), and a
`grab_sequence(count)` timeout would have to scale with the caller-supplied `count` to avoid firing
on legitimately long (but healthy) sequences — which weakens exactly the property `@timeout` is
for, since a genuinely stuck sequence and a merely long one become harder to distinguish the larger
`count` gets. Returning immediately keeps `grab_sequence()`'s own timeout tight and meaningful
("did the sequence even start"), while ongoing health is separately observable via
`DataSequenceState` updates -- arguably a better stall detector than one big end-to-end deadline,
since a subscriber can flag "no progress in N seconds" directly instead of waiting for a single
timeout tuned to the worst case.

## `BaseCamera` implementation

- `grab_sequence(count)`: if `count_left > 0` (sequence already running) or camera isn't idle,
  raises `CameraException`; otherwise spawns `_run_sequence` as a background task and returns.
- `_run_sequence(count_total, broadcast)`: loops calling the existing `grab_data(broadcast)`
  (not `__expose()` directly -- this reuses all of `grab_data()`'s FITS-header/broadcast/upload
  logic unchanged, so a single image taken via a count-1 sequence behaves identically to a plain
  `grab_data()` call) while `count_left > 0`, pushing `DataSequenceState` after each grab; a failed
  grab (`exc.PyObsError`) stops the sequence early instead of propagating. Always finishes by
  pushing `DataSequenceState(0, 0)`, whether it ran to completion, was aborted, or a grab failed.
- `abort_sequence()`: just zeroes `count_left` -- does *not* touch `self.expose_abort`, so a
  currently-running exposure is left alone and finishes normally, and the loop's next iteration
  check stops it there.
- `abort()`: extended with one line to also zero `count_left`, alongside its existing
  `self.expose_abort.set()` -- so a plain `abort()` during a sequence stops everything in one call.
  `abort()` implies `abort_sequence()`'s effect on the count, plus the immediate exposure
  cancellation `abort_sequence()` deliberately doesn't do.
- A hypothetical `ISpectrograph`-side implementation would follow the identical shape, looping
  its own internal grab path instead -- only `BaseCamera` was implemented because that's the
  motivating case, not because the interface is camera-specific.

## GUI-side implication (not implemented, but the motivating case)

`CameraWidget.expose()`'s `while self.exposures_left > 0: ...` loop could become one
`proxy.grab_sequence(n)` call plus a `subscribe_state(module, IDataSequence, ...)` callback
driving the progress display — same shape as how `ExposureState` already drives the existing
progress bar, just one level up. The existing `abort()`'s `if exposures_left > 1: ... else: ...`
branch collapses to a direct call: "Abort sequence" button → `abort_sequence()`, "Abort exposure"
button → `abort()` — no more client-side branching on how many exposures are left.

## Resolved

- Naming: implemented as `count_total`/`count_left`, image/spectrum-agnostic as intended.
- Per-grab callback/event: nothing new added -- `NewImageEvent`/`NewSpectrumEvent` already cover
  this, as expected.

## Still open (not resolved by the implementation)

- Inter-grab behavior (delays, dithering/offsets between images) is out of scope here — that's a
  scheduler/pointing-layer concern, not something `IDataSequence` itself should own.
- `grab_sequence(count=1)` and `grab_data()` remain two separate, permanently-supported entry
  points for now; whether `grab_data()` should eventually be deprecated in favor of always using
  `grab_sequence(1)` was not decided and wasn't part of this implementation.
- The `pyobs-gui` `CameraWidget.expose()` client-side loop was not migrated to `grab_sequence()` --
  the GUI-side implication above is still just a sketch, not implemented.
