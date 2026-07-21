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
