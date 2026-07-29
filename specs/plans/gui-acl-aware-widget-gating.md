# Plan: `pyobs-gui` ACL-aware widget gating

Status: implemented, closed. Option B implemented and verified end-to-end against pyobs-core
2.0.0.dev11 (the first release with ACL support).
Repos: pyobs-gui (all implementation here), pyobs-core (ACL feature it depends on, already shipped)

## Implemented

`BaseWidget._fetch_permitted_methods()` / `BaseWidget.permitted()`
(`base.py`) fetch and cache `IModule.get_permitted_methods()` once per widget, guarded by
`hasattr(IModule, "get_permitted_methods")` so it's a no-op against any older pinned pyobs-core
(>=2.0.0.dev6) that predates the feature — `permitted()` then falls back to "everything allowed."
Wired into `filterwidget.py`, `modewidget.py`, and `telescopewidget.py` (buttons, `move()` branches,
and `compassmovewidget`'s enable state). Fully-denied modules are hidden from the sidebar via the
same `get_permitted_methods()` fetch in `mainwindow.py:_client_connected`.

Verified with two new fixtures, `test/telescope_acl.yaml` (`acl: allow: {gui: [init, move_radec,
set_offsets_radec]}`) and `test/telescope_acl_denied.yaml` (`acl: allow: {gui: []}`), driven via a
`LocalComm`-backed harness (no pytest suite exists in this repo) that opens the real `GUI` module
against a real ACL-enforcing `DummyTelescope` and inspects live widget state:
- `telescope_acl.yaml`: `_permitted_methods` came back exactly `{init, move_radec,
  set_offsets_radec}`; every button/branch gated on a permitted method stayed enabled
  (`buttonMove`, `buttonSetRaOffset`, `buttonSetDecOffset`, `buttonResetEquatorialOffsets`,
  `compassmovewidget`, `permitted("move_radec")`), every one gated on a denied method was forced off
  (`buttonPark`, `buttonSetAltOffset`, `buttonSetAzOffset`, `buttonResetHorizontalOffsets`,
  `permitted("move_altaz")`) — cross-checked with `motion_status=idle` so state-based gating alone
  wouldn't explain the result.
- `telescope_acl_denied.yaml`: `MainWindow._client_connected` returned `False` for the telescope
  client and it never entered `_widgets`, confirming the fully-denied module never reaches the
  sidebar.

<details>
<summary>Original planning notes</summary>

`pyobs-core` 2.0's per-module access control has landed on its `develop` branch: Phase 8 is
implemented in full (`exc.ForbiddenError`, `acl:` config parsing, the `Module.execute()` check,
`IModule.get_permitted_methods()`, XMPP `forbidden`-condition mapping) — confirmed directly against
`pyobs-core`'s code and tests (`pyobs/interfaces/IModule.py`, `pyobs/modules/module.py:388-390,597`,
`tests/modules/test/standalone.py`), not just its own `DEVELOPMENT.md` claims. See its
[Access Control (ACLs)](https://github.com/pyobs/pyobs-core/blob/develop/DEVELOPMENT.md#access-control-acls)
section.

`IModule.get_permitted_methods(**kwargs) -> list[str]` returns the names of methods the *calling*
module is allowed to invoke on the target — caller-specific, always permitted itself (exempted from
its own ACL check), so any widget can call it on its target proxy to ask "what am I allowed to do
here" up front.

**Reactive handling already works today, no change needed:** `BaseWidget._background_task`
(`pyobs_gui/base.py:271-277`) already catches `exc.PyObsError` generically around every RPC call
and routes it to `show_error` (`base.py:282-285`), a plain message box with the exception's text.
`exc.ForbiddenError` is a `RemoteError` is a `PyObsError`, so a denied call already surfaces as a
normal error dialog — confirmed by reading the actual code, not assumed.

**Open, now unblocked — proactive greying-out of unpermitted actions:** widgets already have a
disable/enable mechanism built for a different purpose — `_enable_buttons.emit(disable, False)` /
`w.setEnabled(enable)` (`base.py:268,287-289`) — currently only used to disable buttons while their
own background task is running. The natural fix is to reuse the same mechanism for "not permitted,"
fetched once per widget via `get_permitted_methods()` alongside the capabilities/state it already
pulls from its target proxy at setup, rather than only finding out via an error dialog after the
operator clicks.

**Decided: grey out individual actions, not hide them — except a fully-blocked module, which can be
hidden from the sidebar entirely.** `pyobs-core`'s own design doc hedges throughout ("grey out or
hide") without picking one. Within a widget, the only mechanism it actually points at is the
existing `_enable_buttons` / `setEnabled()` path, which disables widgets — it doesn't remove them
from a layout — and hiding individual buttons would be new machinery (layout changes,
`setVisible(False)` bookkeeping) for no stated benefit, so the per-action plan is disable-only.

But a *module* that's entirely blocked (`get_permitted_methods()` returns `[]` for this GUI's
identity) is a different case, and there hiding is both possible and natural: `mainwindow.py`'s
`_client_connected` (376-424) already has an early-return "ignore it?" gate for `show_modules`
allowlisting, right before a module gets a widget or a nav entry at all
(`mainwindow.py:381-383`) — before `_add_client` runs, so before `self.listPages.addItem(item)`
(`mainwindow.py:241-270`). A "fully denied" check slots into the exact same spot: fetch
`get_permitted_methods()` once per newly-connected client, and if it comes back empty, `return
False` there instead of building a widget for it — the module never appears in the sidebar/nav list
at all, not merely greyed out. This reuses the identical pattern already in place for
`show_modules`, so it's cheap to add alongside the per-widget button work below, not a separate
design.

**Granularity: fetch per-widget, apply per-button — not a single per-widget on/off switch.** Two
things are independent:

- **The `get_permitted_methods()` fetch is per-widget** (really per-target-proxy): each widget
  already talks to one module via `self.comm.proxy(self.module, ...)`, so it fetches once at setup,
  alongside the state/capabilities it already pulls there.
- **The enable/disable decision is per-button.** Widgets already have fine-grained, per-button
  `setEnabled()` calls keyed to current state — e.g. `telescopewidget.py:266-294`:
  `self.buttonInit.setEnabled(self._motion_status == MotionStatus.PARKED)`,
  `self.buttonPark.setEnabled(...)`, `self.buttonStop.setEnabled(...)`. Each button maps to a
  different RPC method (`init`, `park`, `stop`, `move_radec`, ...), often on a different interface
  (`IMotion`, `IPointingRaDec`, `IOffsetsAltAz`, ...) even within the same widget. ACL greying is a
  second condition ANDed into each existing check — e.g.
  `buttonPark.setEnabled(initialized and "park" in self._permitted_methods)` — not a single
  "is this whole widget permitted" switch.

**Concrete surface: only widgets that already gate buttons on background tasks.** Grepping
`run_background(` with a `disable=` argument across `pyobs_gui/*.py` finds exactly four files with
actionable buttons to gate: `telescopewidget.py` (6 call sites), `filterwidget.py`, `modewidget.py`,
`compassmovewidget.py`. Not every `BaseWidget` subclass needs this — several
(`weatherwidget.py`, `datadisplaywidget.py`, `eventswidget.py`, etc.) are read-only displays with no
actions to gate at all.

### Option A: reactive-only (already shipped, zero work)

The reactive path needs no new code at all — confirmed by reading `base.py`, not assumed:

- Every RPC call goes through `BaseWidget._background_task` (`base.py:271-277`), which already
  wraps `await method(*args, **kwargs)` in `try/except exc.PyObsError as e: await
  self.show_error(e)`.
- `show_error` (`base.py:282-285`) already pops a `QAsyncMessageBox.warning` with the exception's
  own text.
- A denial surfaces client-side as `exc.RemoteError(sender, f"Forbidden to invoke {method} at
  {target}!")` (`pyobs-core`'s `pyobs/comm/xmpp/rpc.py:299`) — a `RemoteError` is a `PyObsError`, so
  it's already caught by the generic handler above with a reasonable message.

Net: zero implementation. The only "work" is a manual smoke test against an ACL-restricted module
to confirm the dialog text reads sensibly. Weaker UX than greying out (the operator can still click
into a wall instead of seeing the action disabled up front), but it's the free fallback and already
covers the "reactive handling" bullet above.

### Option B: proactive greying-out — effort estimate (~half a day, 3-5 hours)

Bigger than Option A, but still small — no new architecture, just extending gating logic that
already exists in four files:

1. **Fetch (~30 min).** `get_permitted_methods()` lives on `IModule`, not on `Comm` like the cheap
   `get_interfaces()`/`get_capabilities()` calls, so it needs an actual proxy round trip:
   `async with self.comm.proxy(self.module, IModule) as proxy: permitted =
   set(await proxy.get_permitted_methods())`. Mirrors the existing pattern at
   `telescopewidget.py:144` (`self._interfaces = await self.comm.get_interfaces(self.module)`),
   fetched once in `_init()`/`open()`. Worth a shared helper on `BaseWidget` so the four widgets
   don't duplicate the round trip.

2. **Wiring into existing per-button gating (~1.5-2.5 hours, mostly `telescopewidget.py`).**
   - `filterwidget.py`, `modewidget.py`: trivial — one `setEnabled()` call site each, already gated
     on state; AND in `"set_filter" in self._permitted` / `"set_mode" in self._permitted`.
   - `compassmovewidget.py`: **no internal changes needed** — already gated as a whole block by its
     parent, `self.compassmovewidget.setEnabled(initialized)` at `telescopewidget.py:288`. Just AND
     the relevant offset method's permission into that one line.
   - `telescopewidget.py`: the real work — ~8-10 buttons (`buttonInit`, `buttonPark`, `buttonStop`,
     `buttonMove`, 4x offset buttons, 2x reset-offset buttons), each needing its existing
     `update_gui()` `setEnabled()` line extended with a permission check. `buttonMove` is the one
     wrinkle: it maps to 4 different RPC methods (`move_radec`/`move_altaz`/`move_hgs`/
     `move_helioprojective`) depending on the selected coordinate tab — but `move()`
     (lines 328-392) already branches per-coordinate-type at click time and pops a
     `QMessageBox.critical` for unsupported types, so the permission check slots into that existing
     branch rather than requiring new architecture.

3. **Verification (~1 hour).** UI behavior, not something type-checking catches — needs a manual
   pass (or a `LocalComm`-backed integration test) against a module with an `acl:` block denying a
   couple of methods, confirming the right buttons actually grey out.

Option A is a strict subset of Option B's work, so nothing here is wasted if Option B follows later.

</details>
