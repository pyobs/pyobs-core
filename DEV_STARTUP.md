# Gating RPC commands until module startup completes

## Problem

Some modules (e.g. camera drivers like FLI) take a while to boot: connecting
to hardware, enabling cooling, etc. During that window the module is already
reachable over XMPP and will accept and execute incoming RPC commands, even
though it isn't fully initialized yet.

Example log — the module is connected and publishing capabilities well
before it's actually ready:

```
2026-07-17 19:23:41,057 [INFO] (fli) application.py:226 Opening module...
2026-07-17 19:23:41,290 [INFO] (fli) bind.py:59 JID set to: fli230@monet.saao.ac.za/pyobs
2026-07-17 19:23:41,291 [INFO] (fli) xmppclient.py:131 Connected to server.
2026-07-17 19:23:44,022 [INFO] (fli) xmppcomm.py:905 Published capabilities for IModule
2026-07-17 19:23:44,022 [INFO] (fli) xmppcomm.py:905 Published capabilities for IConfig
2026-07-17 19:24:03,727 [INFO] (fli) flibase.py:70 Opening connection to "ProLine PL230" at /dev/fliusb0...
2026-07-17 19:24:03,730 [INFO] (fli) flicamera.py:54 Connected to camera with serial number: PL0475014
2026-07-17 19:24:03,730 [INFO] (fli) flicamera.py:185 Enabling cooling with a setpoint of 20.00°C...
2026-07-17 19:24:03,786 [INFO] (fli) xmppcomm.py:905 Published capabilities for IWindow
2026-07-17 19:24:03,810 [INFO] (fli) xmppcomm.py:905 Published capabilities for IBinning
2026-07-17 19:24:03,822 [INFO] (fli) application.py:228 Started successfully.
```

Capabilities are published, and the RPC handler is live, ~20 seconds before
`"Started successfully."` — there is currently no guard preventing commands
from executing in that window.

## Where the dispatch happens

`Module.execute()` (`pyobs/modules/module.py:523`) is the single choke point
for all incoming RPC calls, regardless of transport:

- XMPP: `RPC._on_jabber_rpc_method_call` (`pyobs/comm/xmpp/rpc.py:232`) calls
  `self._handler.execute(...)`, where `self._handler` is the `Module`
  instance (wired up in `XmppComm._connect()`, `xmppcomm.py:262-263`, which
  runs at the very start of `Module.open()`).
- In-process / `MultiModule`: `LocalComm.execute()`
  (`pyobs/comm/local/localcomm.py:50-55`) calls
  `remote_client.module.execute(...)` — same method.

A guard added in `Module.execute()` covers both transports with one change.

`Module.execute()` already has two guards in the same style we'd want to
copy:

```python
# pyobs/modules/module.py
542  # is module in error state?
543  if self._state == ModuleState.ERROR:
544      # if called method is not from IModule, raise error
545      if not hasattr(IModule, method):
546          raise exc.ModuleError("Module is in error state, please reset it.")
...
558  if method != "get_permitted_methods" and self._acl_denied(sender, method):
559      if self._acl_mode == "enforce":
560          raise exc.ForbiddenError(
561              f"Caller '{sender}' is not permitted to invoke '{method}'.",
562              sender=sender, method=method, module=sender,
563          )
```

## Where "fully started" actually happens

`Application._main()` (`pyobs/application.py:220-231`):

```python
220  async def _main(self) -> None:
224      try:
225          # open module
226          log.info("Opening module...")
227          await self._module.open()
228          log.info("Started successfully.")
230          # run module
231          await self._module.main()
```

`"Started successfully."` is logged only after `await self._module.open()`
returns — i.e. after the **entire** override chain (base `Module.open()` +
every subclass's `open()`) has finished. This is the true "ready" signal.

### Why `Object._opened` / `Module.opened` is *not* the right flag

`Module` extends `Object`, which has:

```python
# pyobs/object.py
340  self._opened = False
...
365  async def open(self) -> None:
379      self._opened = True
...
386  @property
387  def opened(self) -> bool:
388      return self._opened
```

But concrete module subclasses call the base `open()` as the *first*
statement of their own override and keep doing device-specific setup
*afterward*, e.g. `pyobs/modules/camera/basecamera.py:114-129`:

```python
114  async def open(self) -> None:
115      await Module.open(self)          # <-- self._opened already True here
116      # subscribe to events
118      if self._comm:
119          await self.comm.register_event(NewImageEvent)
...
124      # publish initial states
125      await self.comm.set_state(...)
```

So `self.opened` flips `True` while the FLI driver is still between
`"Opening connection to..."` and `"Started successfully."` in the log above.
Using it as the readiness guard would still let commands through mid-boot —
it does not match what the user is asking to gate on.

## Proposed design

1. Add a new `asyncio.Event` on `Module`, e.g. `self._startup_complete`.
   Mirrors the existing shutdown flag `self._closing = asyncio.Event()`
   (`module.py:159`), which is checked the same way elsewhere (e.g.
   `xmppcomm.py:305: if self._closing.is_set(): return`).

2. Set it in `Application._main()` right after `await self._module.open()`
   returns (`application.py:228`), e.g. via a small public method such as
   `Module._mark_started()` — this is the exact point that currently logs
   `"Started successfully."`.

3. Guard in `Module.execute()`: if `not self._startup_complete.is_set()`,
   raise a `PyobsError` subclass, following the same style as the
   `ModuleState.ERROR` / ACL checks above. Exempt a small whitelist of
   introspection methods that should still work during startup —
   `get_permitted_methods`, `get_version`, `reset_error` (the same ones
   already special-cased around `IModule` in the existing guards).

4. No XMPP-side wiring is required beyond raising the right exception type:
   `rpc.py`'s generic fault handler (`rpc.py:243-251`) already serializes any
   `PyobsError` back to the caller and reconstructs it via
   `RPC._on_jabber_rpc_method_fault` (`rpc.py:283-311`). A dedicated XEP-0009
   condition (mirroring the `ForbiddenError` fast-path at `rpc.py:239-241`)
   would only be needed if callers should be able to distinguish "not ready
   yet" from a generic error/retry.

## Other relevant context found during research

- `IModule` (`pyobs/interfaces/IModule.py`) currently only declares
  `reset_error` and `get_permitted_methods` — no readiness concept.
  `get_version`/`get_label` are plain `Module` methods, not on `IModule`, so
  they are *not* currently covered by the `hasattr(IModule, method)`
  exemption at `module.py:545` and would need to be added explicitly to any
  new whitelist.
- `ModuleState` (`pyobs/utils/enums.py:12-25`) only has `CLOSED`, `READY`,
  `ERROR`, `LOCAL` — no `STARTING`/`OPENING` state, and `Module._state`
  defaults to `READY` at construction (`module.py:152`), before `open()`
  even runs. It cannot currently distinguish "still starting" from "fully
  up," so it can't be reused as the readiness signal either.
- `IReady` / `ReadyState` (`pyobs/interfaces/IReady.py`,
  `pyobs/mixins/motionstatus.py`) is a *domain-level* "ready for science"
  concept (e.g. telescope tracking settled), unrelated to RPC-dispatch
  readiness — don't conflate the two.
- There's already a `ModuleOpenedEvent` (`pyobs/events/moduleopened.py`),
  sent by `XmppComm` when a *client* connects (`xmppcomm.py:570`) and
  handled by `Module._on_module_opened` (`module.py:355`) — this is about
  peer-discovery/announcing presence to other modules, not about the local
  module's own startup completion. Not directly reusable for this guard.

  **Correction (superseded an earlier, wrong claim in this doc):** it was
  initially assumed that `_on_module_opened` (`module.py:353-366`) calling
  `proxy.get_capabilities(IModule)` (`module.py:360-361`) would break against
  the new `STARTING` guard, since `get_capabilities` isn't on the `execute()`
  whitelist. That's incorrect — `Proxy.get_capabilities()`
  (`comm/proxy.py:189-191`) is *not* an RPC call through `Module.execute()`
  at all. It's a synchronous read of a local in-memory cache
  (`self._capabilities`), populated asynchronously whenever a
  capabilities-publish event arrives from the server (disco/PEP push). It
  can never raise against the `STARTING` guard, because it never reaches it.

  The real reason to still delay presence is a **capability-publish race**,
  not RPC rejection. Inside `Module.open()` (`module.py:285-321`): (1)
  `self.comm.open()` connects and, today, sends presence immediately; (2)
  base `IModule`/`IConfig` capabilities are published (`module.py:310-321`);
  (3) subclass `open()` overrides run afterward, which is where
  hardware-dependent capabilities get published — e.g. a camera module
  publishing `IWindow`/`IBinning` only once the sensor is connected and its
  bounds are known (matches the example log: those capabilities appear right
  before `"Started successfully."`, well after `IModule`/`IConfig`). Since
  presence currently fires *before any* capabilities are published, a peer
  reacting to `_got_online` could read `proxy.get_capabilities(IModule)`
  before it's even been published (getting `None` → silently falls back to
  an empty version string rather than crashing) — and the same race applies
  to any device-specific interface a peer might read early. Delaying
  presence until `READY` means that by the time any peer can observe the
  module as online, the entire `open()` chain — including every subclass's
  hardware-dependent capability publish — has already finished, so
  capabilities peers read are always complete and race-free.

## Decisions

1. **Whitelist, not `hasattr(IModule, ...)`.** The existing `ModuleState.ERROR`
   guard (`module.py:542-546`) exempts methods via `hasattr(IModule, method)`,
   but `get_version`/`get_label` aren't declared on `IModule` so that pattern
   would silently exclude them. The new `STARTING` guard in `Module.execute()`
   uses an explicit whitelist tuple instead:
   `("get_permitted_methods", "get_version", "get_label", "reset_error")`.

2. **Add `ModuleState.STARTING`.** New value in `pyobs/utils/enums.py`
   (alongside `CLOSED`, `READY`, `ERROR`, `LOCAL`). `Module._state` is set to
   `STARTING` before `open()` begins (instead of defaulting straight to
   `READY` as it does today at `module.py:152`), and transitions to `READY`
   once `Application._main()`'s `await self._module.open()` returns
   (`application.py:227-228`) — the same point that already logs
   `"Started successfully."`. `Module.execute()` rejects calls (outside the
   whitelist) while `_state == ModuleState.STARTING`.

3. **`IReady` stays untouched.** It's a domain-level "ready for science"
   concept (e.g. telescope settled after a slew) and is orthogonal to
   RPC-dispatch readiness — a module can be `READY` (accepting commands)
   while its `IReady` state is still `False` (e.g. still slewing). No change
   needed here beyond keeping the two concepts separate.

4. **Delay `send_presence()` until `READY`.** Not a command-execution guard
   (that's fully handled by `Module.execute()`'s `STARTING` check, decision
   #2, independent of transport or presence) — this is about eliminating the
   **capability-publish race** described above. Currently
   `XmppClient.session_start()` calls `self.send_presence()` immediately on
   XMPP connect (`xmppclient.py:134`), which is what makes the module visible
   to peers' `_got_online` → `ModuleOpenedEvent` → `_on_module_opened` chain
   — long before the module's own `open()` override chain, and thus its
   hardware-dependent capability publishes, have finished. Holding
   `send_presence()` until `Module` signals it has reached `READY` means the
   module stays connected to the XMPP server but invisible to peer discovery
   until fully booted, so any capabilities a peer reads afterward are
   guaranteed complete. This requires plumbing a readiness signal from
   `Module` down into `XmppClient` (the two are presently decoupled —
   `XmppClient` has no visibility into `Module._state`).

## Implementation

Landed on `feature/startup-gating`. Deviated from the plan above in a few
places, discovered only by testing against a live local ejabberd server —
worth recording since they weren't visible from code reading alone:

- **`get_version`/`get_label` dropped from the `STARTING` whitelist.**
  Neither is declared on `IModule`, so neither ever appears in
  `Module._methods` (populated only from registered `Interface` methods) --
  they were never reachable via `execute()` at all, whitelisted or not.
  Whitelist trimmed to `("get_permitted_methods", "reset_error")`, the only
  two methods actually callable through `execute()`.

- **`Module.start()` added, not just `Application` calling `open()` then
  `set_state(READY)`.** `MultiModule._run_module()` (`module.py`) calls
  `await mod.open()` directly for each sub-module, with no follow-up
  `set_state(READY)` -- under the original plan every module running inside
  a `MultiModule` process would stay `STARTING` forever, rejecting all
  RPC calls. Fixed by adding `Module.start()` (`open()` then
  `set_state(READY)`) and having both `Application._main()` and
  `MultiModule._run_module()` call it instead of `open()` directly.

- **Presence gating had to become opt-in per-comm, not global per-client.**
  The original design gated every `XmppClient.send_presence()` call behind
  `mark_ready()`. Verified against a live local ejabberd
  (`tests/integration/`, `-m xmpp`): this silently broke presence for any
  module-less `XmppComm` too -- e.g. the `observer` comm used throughout the
  integration test suite, which has no `Module` attached and thus never
  calls anything that triggers `mark_ready()`. Its own presence broadcast
  never went out, which broke the mutual-subscription exchange that
  delivers *other* peers' presence to it, independent of anything `camera`
  did. Fixed in `XmppComm._connect()`: a freshly created client is marked
  ready immediately unless `self.has_module` is true and the module hasn't
  reached `READY` yet (`self._module_ready`) -- gating now applies only to
  an actual starting `Module`, not to bare/GUI/observer-style `XmppComm`
  usage, which behaves exactly as before.

- One integration test (`test_set_state_automatically_updates_presence`)
  had to be reordered: it originally asserted peer visibility appearing
  *after* the observer was already connected and the module announced
  itself for the first time only afterward via `set_state()`. That specific
  sequence -- a first "come online" broadcast reaching a subscriber that
  connected before the peer ever announced -- isn't reliably delivered by
  this test environment's roster/subscription setup (never previously
  exercised, since presence used to go out immediately on connect, always
  before any observer could possibly connect first). Fixed by establishing
  `READY` visibility before exercising the `ERROR` update the test is
  actually about, matching every other peer-discovery test in the suite.

## Follow-up questions & resolutions

Raised after the initial decisions, while thinking through implementation
details:

- **Does `LocalComm`/`MultiModule` need the same presence-delay treatment?**
  No — confirmed not applicable. `LocalComm._register_events()` is a no-op
  (`localcomm.py:71: pass`), so `ModuleOpenedEvent`/`_on_module_opened`
  peer-discovery never fires under `LocalComm` — it's XMPP-only. Also,
  `LocalComm.__init__` calls `self._network.connect_client(self)` immediately
  at construction (`localcomm.py:21`), making a module visible via `.clients`
  before `open()` even starts — there's no presence concept there to gate.
  `LocalComm` callers are protected solely by the `Module.execute()`
  `STARTING` guard, which already covers them via
  `LocalComm.execute()` → `remote_client.module.execute(...)`
  (`localcomm.py:50-55`).

- **How does `Module` signal `READY` down to `XmppClient`?** Add a method on
  `Comm` (e.g. `Comm.mark_ready()`), implemented by `XmppComm`/`XmppClient` to
  fire the deferred `send_presence()`. `Module` calls it once `_state`
  transitions to `READY` in `Application._main()`. Base `Comm` gets a no-op
  default so `LocalComm` and other transports don't need to implement it.

- **Reconnect behavior.** `XmppClient.session_start()` fires on every
  reconnect, not just the first connect. Resolution: send presence
  immediately if the module is already `READY`; only hold it back while the
  module is still `STARTING`. Otherwise a brief network blip on an
  already-running module would make it vanish from peer discovery.

- **Guard ordering in `Module.execute()`.** `STARTING` is checked first,
  ahead of the existing `ModuleState.ERROR` check (`module.py:542-546`) and
  the ACL check (`module.py:558-567`).

- **What if `open()` itself raises?** No fix needed. Checked
  `Application._main()` (`application.py:220-231`): it runs exactly once per
  process (`_run()` → `run_until_complete`, no retry/reconnect loop around
  it); on an `open()` exception it logs, falls through to `finally`, calls
  `close()`, and the process exits shortly after. Combined with the
  presence-delay decision above, a module whose `open()` fails never sent
  presence in the first place, so no peer could ever have observed it stuck
  in `STARTING` — the state is unobservable and the process is gone moments
  later anyway.
