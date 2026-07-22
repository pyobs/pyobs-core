# Blocking vendor SDK calls must never run directly on the event loop

Every pyobs module runs its own async code on a single-threaded event loop. A driver author
writing a hardware module inevitably has to call into a vendor SDK — a camera library, a mount
controller's protocol library, whatever the actual device exposes — and those calls are almost
always plain, synchronous, blocking C/C-extension/GLib calls with no `async`/`await` involved at
all. Calling one of those *directly* from an `async def` method — even one that's supposed to be
non-blocking by the vendor's own documented behavior — freezes the entire module for however long
that call actually takes. Not just the method that made the call: every other coroutine on the
same event loop, including the module's own XMPP keepalive, its ability to respond to any other
module's requests, and its own outgoing calls, all stall for the same duration.

This has been found independently, twice, in two unrelated driver projects, each time initially
dismissed as "that call is basically instant, it can't matter":

- **`pyobs-aravis`**: `AravisCamera.open()` called `aravis.get_device_ids()` — a network-based
  broadcast discovery (GigE Vision devices reply to a query over the wire) that can legitimately
  take multiple seconds — directly on the event loop. Separately, `_capture()`'s polling loop
  called `self._camera.pop_frame()` the same way, in a tight loop with a `sleep(0.01)` between
  attempts assuming the call itself was instant. Neither assumption reliably holds under real
  network/hardware conditions (camera hiccup, GigE stall). Fixed by running the call in a
  dedicated thread via `_run_blocking()` (one-shot calls like `open()`/`close()`) or
  `_wait_for_frame()` (the polling case — see below for why that one needed a different shape).
- **`pyobs-fli`**: `FliBaseMixin.open()` calls `FliDriver.list_devices()` and `driver.open()` the
  same unguarded way. This one hasn't caused an observed production problem yet, purely because
  FLI's device enumeration is a local USB/PCI bus scan rather than a network round-trip, so the
  actual blocking duration is negligible in practice. The bug is structurally identical; only the
  consequence differs, and only because of what hardware happens to be on the other end today.

The pattern to follow is `pyobs_aravis.araviscamera.AravisCamera._run_blocking()`: run the
blocking call in a plain `threading.Thread(daemon=True)` (not a shared executor — see its own
docstring for why: executor worker threads are non-daemon and get joined at interpreter
shutdown, so a permanently-hung call would just move the freeze to process exit instead of
avoiding it), signal completion back to the event loop via `loop.call_soon_threadsafe`, and bound
the wait with `asyncio.wait_for(..., timeout=...)` so a truly hung call can't block the caller
forever either — it times out, logs, and the module can decide how to recover (see
`_activate_camera`/`_deactivate_camera` for the "log and null out the reference" shape).

One thing that pattern doesn't cover as-is: **a call that's polled at high frequency** (e.g.
`pop_frame()`, called up to ~100x/s while waiting for the next frame at a 10ms poll interval).
Spawning a fresh thread per poll would trade one problem (blocking the event loop) for another
(thread-creation overhead on every single poll, most of which are expected to return
immediately). The fix there — `_wait_for_frame()` in `pyobs-aravis` — runs the *entire*
"poll until ready" loop as a single blocking function, so only one thread gets spawned per
delivered frame, not one per 10ms attempt. Reach for this shape, not
`_run_blocking()` directly, whenever the blocking call in question is itself invoked in a tight
polling loop rather than once per meaningful operation.

**When writing or reviewing a driver module**: any call into a vendor SDK/library that isn't
itself `async` needs one of these two treatments before it ships, regardless of how fast the
vendor's documentation claims it is — "it's basically instant" is exactly the assumption that
was wrong both times this was found. If the call happens once per operation (connect, open,
close, a single command), use `_run_blocking()`. If it's polled repeatedly waiting for a
condition, wrap the whole wait loop and use the one-blocking-call-per-outcome shape instead.

## Fleet-wide survey (2026-07-22)

Given the pattern had already turned up twice independently, every sibling driver repo under
`../` was checked for the same shape (`async def` methods — especially `open()`/`close()`/
polling loops — calling a synchronous vendor SDK directly, unwrapped). It's widespread. Not
fixed yet anywhere except the two projects noted above, and even one of those has a gap:

- **`pyobs-asi`**: `AsiCamera.open()` calls `asi.init()`/`get_num_cameras()`/`list_cameras()`/
  `Camera()`/`get_camera_property()` directly. `_expose()`'s wait loop polls
  `self._camera.get_exposure_status()` every 10ms — same tight-poll-of-a-blocking-call shape as
  `pop_frame()`.
- **`pyobs-flipro`**: structurally identical to the already-documented `pyobs-fli` case.
  `FliProCamera.open()` calls `FliProDriver.list_devices()`/`self._driver.open()` directly;
  `_wait_exposure()` tight-polls `self._driver.is_available()`. No `_run_blocking()` anywhere in
  the repo.
- **`pyobs-zwoeaf`**: `EafFocuser.open()` calls the ZWO EAF SDK's `connect()`/`setMaximalStep()`/
  `setBacklash()`/`setDirection()`/`setSound()`/`getTemperature()`/`getPosition()` directly;
  `set_focus()` tight-polls `self._eaf.isMoving()` every 0.5s. `close()` and the temperature-poll
  background task have the same problem.
- **`pyobs-v4l`**: `_capture()`'s background task calls `cv2.VideoCapture(...)` and
  `camera.read()` directly — plain blocking OpenCV/V4L2 calls, never wrapped.
- **`pyobs-zaber`** (narrow): the rest of the driver correctly uses `zaber_motion`'s real async
  API (`open_serial_port_async`, `move_relative_async`, ...), but `enable_led()` (called from
  `open()`) uses the library's *synchronous* `device.settings.set()` instead of the
  `set_async()` variant the same library exposes — the one call in an otherwise-correct file
  that reverts to the blocking pattern.
- **`pyobs-monet`**: the clearest case found. `bonnshutter.py` has had a
  `# TODO: find a way for serial to work with asyncio!` comment sitting on it — `send_to_shutter()`,
  `get_status()`, and `_reset_shutter()` are all `async def` but open a plain blocking
  `serial.Serial(...)` and do synchronous `ser.write()`/`ser.readline()` directly on the event
  loop. `get_status()` runs from a 60s background poll and from every exposure via
  `ensure_blade_open()`/`expose()`, so this stalls the module on a cadence, not just at startup.
  The four camera+shutter composites in the same repo (`qhyccd_bonnshutter.py`,
  `sbig_bonnshutter.py`, `fli_bonnshutter.py`, `flikepler_bonnshutter.py`) inherit this plus
  whatever their underlying camera driver has, without adding new unwrapped calls of their own.
- **`pyobs-iagvt`**: mixed. `modules/solartelescope.py`'s `Siderostat` (SSH-based) is done right
  — every call goes through its own `_run_blocking()` consistently. `modules/gregorycamera.py`
  correctly inherits `AravisCamera`'s `_wait_for_frame()`. But `modules/fibercamera.py`, also an
  `AravisCamera` subclass, adds `set_gain()`/`_get_gain()` calling `self._camera.set_feature()`/
  `get_feature()` directly instead of routing through the inherited `_run_blocking()` — a
  regression introduced locally in a file that had the correct helper available.
- **`pyobs-qhyccd`** and **`pyobs-sbig`**: only *partially* fixed. Both correctly wrap the
  actual frame readout (`get_single_frame` / `readout`) in `run_in_executor`. But `open()` in
  both (device enumeration, link establishment, chip info) and the cooling-poll background tasks
  are still unwrapped, direct SDK calls; `pyobs-sbig`'s exposure-wait loop
  (`while not self._cam.has_exposure_finished(): await asyncio.sleep(0.01)`) and
  `sbigfiltercamera.py`'s filter-position poll have the same tight-poll shape as `pop_frame()`.
- Even **`pyobs-aravis` itself** — the repo this fix originated in — has one residual gap:
  `AravisCamera.set_exposure_time()` calls `self._camera.set_exposure_time(...)` directly,
  unwrapped by `_run_blocking()`.

Checked and found **not applicable** (already genuinely async, e.g. `aiohttp`/`aiomqtt`/
`aioserial`-based, or no hardware SDK involved): `pyobs-alpaca`, `pyobs-brot`, `pyobs-iag50`,
`pyobs-monti`, `pyobs-polaris`, `pyftscontrol`, and the non-camera modules of `pyobs-iagvt`
(`led.py`, `ldp.py`, `suncamera.py`).

This is a punch list, not a mandate to fix everything at once — but any future touch of these
files should route the call through `_run_blocking()`/the wait-loop shape rather than leaving
the existing unwrapped call in place "since it's already like that."
